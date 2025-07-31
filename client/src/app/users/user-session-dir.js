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

    var app = angular.module('users.directives.user-session', [
        'ui.bootstrap',
        'users.controllers.user-session'
    ]);

    /**
     * Login Modal Service
     */
    app.service('loginModal', function($uibModal, $rootScope) {
        function assignCurrentUser(user) {
            $rootScope.currentUser = user;
            return user;
        }
        
        return function() {
            var instance = $uibModal.open({
                templateUrl: 'app/users/user-sign-in.tpl.html',
                backdrop: 'static',
                keyboard: false
            });
            
            return instance.result.then(assignCurrentUser);
        };
    });

    /**
     * Session Toolbar Directive
     * Modern responsive user session toolbar
     */
    app.directive("sessionToolbar", function() {
        return {
            restrict: 'E',
            replace: true,
            template: `
                <div class="session-toolbar" ng-if="userInfo.email">
                    <div class="dropdown">
                        <button class="btn btn-outline-light dropdown-toggle" type="button" 
                                data-bs-toggle="dropdown" aria-expanded="false">
                            <i class="fas fa-user-circle me-1"></i>
                            <span class="d-none d-md-inline">{{userInfo.email}}</span>
                            <i class="fas fa-chevron-down ms-1"></i>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li>
                                <h6 class="dropdown-header">Signed in as {{userInfo.email}}</h6>
                            </li>
                            <li><hr class="dropdown-divider"></li>
                            <li>
                                <a class="dropdown-item" href="#" ng-click="userSession.signOutButtonHandler()">
                                    <i class="fas fa-sign-out-alt me-2"></i>
                                    Sign out
                                </a>
                            </li>
                            <li>
                                <a class="dropdown-item" href="{{GALAXY_SERVER_URL}}" target="_blank">
                                    <i class="fas fa-external-link-alt me-2"></i>
                                    Go to Galaxy site
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>
            `
        };
    });

    /**
     * Password Match Directive
     * Validates that password confirmation matches original password
     */
    app.directive("ngPwcheck", [function() {
        return {
            require: 'ngModel',
            link: function(scope, elem, attrs, ctrl) {
                var firstPassword = '#' + attrs.ngPwcheck;
                
                elem.on('keyup', function() {
                    scope.$apply(function() {
                        var v = elem.val() === $(firstPassword).val();
                        ctrl.$setValidity('pwmatch', v);
                    });
                });
                
                $(firstPassword).on('keyup', function() {
                    scope.$apply(function() {
                        var v = elem.val() === $(firstPassword).val();
                        ctrl.$setValidity('pwmatch', v);
                    });
                });
            }
        };
    }]);

    /**
     * User Session Info Panel Directive
     * Modern user information panel with disk usage
     */
    app.directive("userSessionInfoPanel", function() {
        return {
            restrict: 'E',
            replace: true,
            template: `
                <div class="user-info-panel" ng-if="userInfo.email">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-user-circle me-2"></i>
                                Your Account
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="info-item">
                                <label class="info-label">Galaxy Server:</label>
                                <span class="info-value">{{GALAXY_SERVER_URL}}</span>
                            </div>
                            <div class="info-item">
                                <label class="info-label">Signed in as:</label>
                                <span class="info-value">{{userInfo.email}}</span>
                            </div>
                            <div class="info-item">
                                <label class="info-label">Username:</label>
                                <span class="info-value">{{userInfo.username || 'Loading...'}}</span>
                            </div>
                            <div class="info-item">
                                <label class="info-label">Disk Usage:</label>
                                <span class="info-value">{{userInfo.disk_usage || "Loading..."}}</span>
                            </div>
                            <div class="text-center mt-3">
                                <button class="btn btn-outline-danger btn-sm" 
                                        ng-click="userSession.signOutButtonHandler()">
                                    <i class="fas fa-sign-out-alt me-1"></i>
                                    Close session
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `
        };
    });
})();
