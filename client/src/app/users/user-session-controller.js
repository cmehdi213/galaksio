/*
* (C) Copyright 2016 SLU Global Bioinformatics Centre, SLU
* (http://sgbc.slu.se) and the B3Africa Project (http://www.b3africa.org/).
*
* All rights reserved. This program and the accompanying materials
* are made available under the terms of the GNU Lesser General Public License
* (LGPL) version 3 which accompanies this distribution, and is available at
* http://www.gnu.org/licenses/lgpl.html
*
* This library is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
* Lesser General Public License for more details.
*
* Contributors:
* Rafael Hernandez de Diego
* Tomas Klingstrom
* Erik Bongcam-Rudloff
* and others.
*
* Modernized for responsive design and enhanced UX
*/

(function() {
    'use strict';

    var app = angular.module('users.controllers.user-session', [
        'ang-dialogs',
        'ui.router',
    ]);

    app.controller('UserSessionController', [
        '$state', '$rootScope', '$scope', '$http', '$timeout', '$dialogs', 'APP_EVENTS',
        function($state, $rootScope, $scope, $http, $timeout, $dialogs, APP_EVENTS) {
            
            var vm = this;
            
            // Initialize scope variables
            $scope.isLogin = true;
            $scope.userInfo = {
                email: Cookies.get("galaxyuser") || '',
                username: '',
                password: '',
                passconfirm: ''
            };
            $scope.isLoading = false;

            //--------------------------------------------------------------------
            // CONTROLLER FUNCTIONS
            //--------------------------------------------------------------------

            /**
             * Get current user details from Galaxy
             */
            this.getCurrentUserDetails = function() {
                if (!Cookies.get("galaxyuser")) {
                    return;
                }

                $scope.isLoading = true;
                
                $http($rootScope.getHttpRequestConfig("GET", "user-info", {
                    headers: {'Content-Type': 'application/json; charset=utf-8'},
                    extra: "current"
                }))
                .then(
                    function successCallback(response) {
                        $scope.userInfo.email = response.data.email;
                        $scope.userInfo.username = response.data.username;
                        $scope.userInfo.disk_usage = response.data.nice_total_disk_usage;
                        
                        // Update cookies
                        Cookies.remove("galaxyusername", {path: getPathname()});
                        Cookies.set("galaxyusername", $scope.userInfo.username, {
                            expires: 1, 
                            path: getPathname()
                        });
                        Cookies.remove("galaxyuser", {path: getPathname()});
                        Cookies.set("galaxyuser", $scope.userInfo.email, {
                            expires: 1, 
                            path: getPathname()
                        });
                        
                        $scope.isLoading = false;
                    },
                    function errorCallback(response) {
                        if (Cookies.get("galaksiosession") === undefined) {
                            return;
                        }
                        
                        console.error("Failed while getting user's details at UserSessionController:signInButtonHandler");
                        console.error(response.data);
                        $scope.isLoading = false;
                    }
                );
            };

            //--------------------------------------------------------------------
            // EVENT HANDLERS
            //--------------------------------------------------------------------

            $scope.$on(APP_EVENTS.loginSuccess, function(event, args) {
                $scope.userInfo.email = Cookies.get("galaxyuser");
                vm.getCurrentUserDetails();
            });

            $scope.$on(APP_EVENTS.logoutSuccess, function(event, args) {
                delete $scope.userInfo.email;
            });

            $scope.$on(APP_EVENTS.logoutRequired, function(event, args) {
                vm.signOutButtonHandler();
            });

            //--------------------------------------------------------------------
            // FORM HANDLERS
            //--------------------------------------------------------------------

            /**
             * Handle form submission (sign in or sign up)
             */
            this.signFormSubmitHandler = function() {
                if ($scope.isLogin) {
                    this.signInButtonHandler();
                } else {
                    this.signUpButtonHandler();
                }
            };

            /**
             * Handle sign in process
             */
            this.signInButtonHandler = function() {
                if (!$scope.userInfo.email || !$scope.userInfo.password) {
                    return;
                }

                $scope.isLoading = true;

                $http($rootScope.getHttpRequestConfig("GET", "user-sign-in", {
                    headers: {
                        "Authorization": "Basic " + btoa($scope.userInfo.email + ":" + $scope.userInfo.password)
                    }
                }))
                .then(
                    function successCallback(response) {
                        // Clean previous cookies
                        Cookies.remove("galaxyuser", {path: getPathname()});
                        Cookies.remove("galaksiosession", {path: getPathname()});
                        Cookies.remove("current-history", {path: getPathname()});

                        // Set new cookies
                        Cookies.set("galaxyuser", $scope.userInfo.email, {
                            expires: 1, 
                            path: getPathname()
                        });
                        Cookies.set("galaksiosession", btoa(response.data.api_key), {
                            expires: 1, 
                            path: getPathname()
                        });

                        $scope.userInfo.email = Cookies.get("galaxyuser");
                        delete $scope.userInfo.password;
                        delete $scope.signForm;

                        // Notify all controllers that user has signed in
                        $rootScope.$broadcast(APP_EVENTS.loginSuccess);
                        
                        // Show success message
                        $dialogs.showSuccessDialog("Successfully signed in!");
                        
                        // Navigate to home
                        $timeout(function() {
                            $state.go('home');
                        }, 1000);
                        
                        $scope.isLoading = false;
                    },
                    function errorCallback(response) {
                        $scope.isLoading = false;
                        
                        if (response.data && [404001, 401001].indexOf(response.data.err_code) !== -1) {
                            $dialogs.showErrorDialog("Invalid email or password.");
                            return;
                        }
                        
                        var message = "Failed during sign-in process.";
                        $dialogs.showErrorDialog(message, {
                            logMessage: message + " at UserSessionController:signInButtonHandler."
                        });
                        console.error(response.data);
                    }
                );
            };

            /**
             * Handle sign up process
             */
            this.signUpButtonHandler = function() {
                if (!$scope.userInfo.email || !$scope.userInfo.username || 
                    !$scope.userInfo.password || $scope.userInfo.password !== $scope.userInfo.passconfirm) {
                    return;
                }

                $scope.isLoading = true;

                $http($rootScope.getHttpRequestConfig("POST", "user-sign-up", {
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    urlEncodedRequest: true,
                    data: {
                        email: $scope.userInfo.email,
                        username: $scope.userInfo.username,
                        password: $scope.userInfo.password,
                        confirm: $scope.userInfo.password,
                        create_user_button: "Submit"
                    }
                }))
                .then(
                    function successCallback(response) {
                        // Parse response for errors
                        var parser = new DOMParser();
                        var doc = parser.parseFromString(response.data, 'text/html');
                        var errorMessage = doc.querySelector('.errormessage');
                        
                        if (!errorMessage || errorMessage.textContent.trim() === '') {
                            $dialogs.showSuccessDialog("Your account has been created successfully!");
                            $scope.isLogin = true;
                        } else {
                            $dialogs.showErrorDialog("Failed when creating new account: " + errorMessage.textContent);
                        }
                        
                        delete $scope.userInfo.password;
                        delete $scope.userInfo.passconfirm;
                        delete $scope.signForm;
                        
                        $scope.isLoading = false;
                    },
                    function errorCallback(response) {
                        $scope.isLoading = false;
                        
                        var message = "Failed during sign-up process.";
                        $dialogs.showErrorDialog(message, {
                            logMessage: message + " at UserSessionController:signUpButtonHandler."
                        });
                        console.error(response.data);
                    }
                );
            };

            /**
             * Handle sign out process
             */
            this.signOutButtonHandler = function() {
                // Clean all cookies
                Cookies.remove("galaxyuser", {path: getPathname()});
                Cookies.remove("galaksiosession", {path: getPathname()});
                Cookies.remove("current-history", {path: getPathname()});
                Cookies.remove("galaxyusername", {path: getPathname()});
                
                // Clean session storage
                sessionStorage.removeItem("workflow_invocations");
                
                // Clear user info
                delete $scope.userInfo.email;
                
                // Redirect to sign in page
                var redirectUrl = getPathname().replace(/\/$/g, "") + "/#/signin?_=" + (new Date()).getTime();
                location.replace(redirectUrl);
                location.reload();
            };

            //--------------------------------------------------------------------
            // INITIALIZATION
            //--------------------------------------------------------------------

            // Get current user details on initialization
            this.getCurrentUserDetails();
        }
    ]);
})();
