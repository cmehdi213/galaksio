(function() {
    'use strict';

    var app = angular.module('b3galaxyApp', [
        'ang-dialogs',
        'ui.router',
        'ngScrollSpy',
        'angular-toArrayFilter',
        'users.directives.user-session',
        'workflows.controllers.workflow-list',
        'workflows.controllers.workflow-run',
        'histories.controllers.history-list',
        'datasets.controllers.dataset-list',
        'admin.controllers.setting-list'
    ]);

    // App Configuration
    app.constant('myAppConfig', {
        VERSION: '0.4.0',
        GALAKSIO_SERVER: "/" + getPathname(),
        API_TIMEOUT: 30000,
        ITEMS_PER_PAGE: 12
    });

    // App Events
    app.constant('APP_EVENTS', {
        loginSuccess: 'auth-login-success',
        loginFailed: 'auth-login-failed',
        logoutSuccess: 'auth-logout-success',
        logoutRequired: 'auth-logout-required',
        sessionTimeout: 'auth-session-timeout',
        notAuthenticated: 'auth-not-authenticated',
        notAuthorized: 'auth-not-authorized',
        historyChanged: 'history-changed',
        updateInvocations: 'update-invocations',
        updatedInvocations: 'updated-invocations',
        updatingInvocations: 'updating-invocations',
        invocationStateChanged: 'invocation-state-changed',
        invocationResultsRequired: 'invocation-results-required',
        showNotification: 'show-notification',
        hideNotification: 'hide-notification'
    });

    // Routing Configuration
    app.config([
        '$stateProvider',
        '$urlRouterProvider',
        '$locationProvider',
        '$httpProvider',
        function($stateProvider, $urlRouterProvider, $locationProvider, $httpProvider) {
            
            // Enable HTML5 mode
            $locationProvider.html5Mode(true);
            $locationProvider.hashPrefix('!');
            
            // HTTP interceptor for loading states
            $httpProvider.interceptors.push(['$q', '$rootScope', function($q, $rootScope) {
                return {
                    request: function(config) {
                        $rootScope.isLoading = true;
                        return config;
                    },
                    response: function(response) {
                        $rootScope.isLoading = false;
                        return response;
                    },
                    responseError: function(rejection) {
                        $rootScope.isLoading = false;
                        return $q.reject(rejection);
                    }
                };
            }]);

            // States
            var states = {
                signin: {
                    name: 'signin',
                    url: '/signin',
                    templateUrl: "app/users/user-sign-in.tpl.html",
                    data: {requireLogin: false, title: 'Sign In'}
                },
                home: {
                    name: 'home',
                    url: '/',
                    templateUrl: "app/home/home.tpl.html",
                    data: {requireLogin: true, title: 'Home'}
                },
                workflows: {
                    name: 'workflows',
                    url: '/workflows',
                    templateUrl: "app/workflows/workflow-list.tpl.html",
                    data: {requireLogin: true, title: 'Workflows'}
                },
                workflowRun: {
                    name: 'workflowRun',
                    url: '/workflow-run/:id',
                    params: {
                        id: null,
                        invocation_id: null
                    },
                    templateUrl: "app/workflows/workflow-run.tpl.html",
                    data: {requireLogin: true, title: 'Run Workflow'}
                },
                workflowDetail: {
                    name: 'workflowDetail',
                    url: '/workflow-detail/:id',
                    params: {
                        id: null,
                        mode: null
                    },
                    templateUrl: "app/workflows/workflow-detail.tpl.html",
                    data: {requireLogin: true, title: 'Workflow Details'}
                },
                histories: {
                    name: 'histories',
                    url: '/histories',
                    templateUrl: "app/histories/history-page.tpl.html",
                    data: {requireLogin: true, title: 'Histories'}
                },
                admin: {
                    name: 'admin',
                    url: '/admin',
                    templateUrl: "app/admin/admin-page.tpl.html",
                    data: {requireLogin: false, title: 'Admin'}
                }
            };

            // Register states
            Object.keys(states).forEach(function(key) {
                $stateProvider.state(states[key]);
            });

            // Default route
            $urlRouterProvider.otherwise('/');
        }
    ]);

    // Main Controller
    app.controller('MainController', [
        '$rootScope', '$scope', '$state', '$http', '$timeout', '$interval', 
        'myAppConfig', 'APP_EVENTS',
        function($rootScope, $scope, $state, $http, $timeout, $interval, 
                 myAppConfig, APP_EVENTS) {
            
            var vm = this;
            
            // Initialize properties
            vm.currentPage = null;
            vm.currentPageTitle = '';
            vm.isAuthenticated = isAuthenticated;
            vm.getCurrentUser = getCurrentUser;
            vm.isLoading = false;
            vm.toasts = [];
            vm.stats = {};
            vm.systemStatus = {};
            vm.recentWorkflows = [];
            
            // Available pages
            vm.getPages = function() {
                return [
                    {name: 'home', title: 'Home', icon: 'fa-home'},
                    {name: 'workflows', title: 'Workflows', icon: 'fa-project-diagram'},
                    {name: 'histories', title: 'Histories', icon: 'fa-history'},
                    {name: 'admin', title: 'Admin', icon: 'fa-cog'}
                ];
            };
            
            // Navigation
            vm.setPage = function(page) {
                $state.transitionTo(page);
                vm.currentPage = page;
                updatePageTitle(page);
            };
            
            vm.logout = function() {
                Cookies.remove('galaxyuser');
                Cookies.remove('galaksiosession');
                $state.go('signin');
                showToast('success', 'Logged Out', 'You have been successfully logged out.');
            };
            
            // Utility functions
            function isAuthenticated() {
                return Cookies.get('galaxyuser') && Cookies.get('galaksiosession');
            }
            
            function getCurrentUser() {
                return Cookies.get('galaxyuser') || 'Guest';
            }
            
            function updatePageTitle(page) {
                var pageConfig = $state.get(page);
                vm.currentPageTitle = pageConfig ? pageConfig.data.title : '';
                document.title = vm.currentPageTitle + ' - Galaksio';
            }
            
            // Toast notifications
            function showToast(type, title, message) {
                var toast = {
                    id: Date.now(),
                    type: type,
                    title: title,
                    message: message,
                    icon: getToastIcon(type)
                };
                
                vm.toasts.push(toast);
                
                // Auto-remove after 5 seconds
                $timeout(function() {
                    removeToast(toast.id);
                }, 5000);
            }
            
            function removeToast(id) {
                vm.toasts = vm.toasts.filter(function(toast) {
                    return toast.id !== id;
                });
            }
            
            function getToastIcon(type) {
                var icons = {
                    success: 'fa-check-circle',
                    error: 'fa-exclamation-circle',
                    warning: 'fa-exclamation-triangle',
                    info: 'fa-info-circle'
                };
                return icons[type] || icons.info;
            }
            
            // API request helper
            $rootScope.getRequestPath = function(service, extra) {
                extra = extra || "";
                var paths = {
                    'user-sign-in': myAppConfig.GALAKSIO_SERVER + "api/authenticate/baseauth",
                    'user-sign-up': myAppConfig.GALAKSIO_SERVER + "api/signup",
                    'user-info': myAppConfig.GALAKSIO_SERVER + "api/users/" + extra,
                    'workflow-list': myAppConfig.GALAKSIO_SERVER + "api/workflows/",
                    'workflow-info': myAppConfig.GALAKSIO_SERVER + "api/workflows/" + extra,
                    'workflow-download': myAppConfig.GALAKSIO_SERVER + "api/workflows/" + extra + "/download",
                    'workflow-run': myAppConfig.GALAKSIO_SERVER + "api/workflows/" + extra + "/invocations",
                    'workflow-import': myAppConfig.GALAKSIO_SERVER + "api/workflows/" + extra,
                    'workflow-delete': myAppConfig.GALAKSIO_SERVER + "api/workflows/" + extra,
                    'workflow-report': myAppConfig.GALAKSIO_SERVER + "other/workflows/report/",
                    'invocation-state': myAppConfig.GALAKSIO_SERVER + "api/workflows/" + extra[0] + "/invocations/" + extra[1] + "?legacy_job_state=true",
                    'invocation-result': myAppConfig.GALAKSIO_SERVER + "api/workflows/" + extra[0] + "/invocations/" + extra[1] + "/steps/" + extra[2],
                    'tools-info': myAppConfig.GALAKSIO_SERVER + "api/tools/" + extra + "/build",
                    'datasets-list': myAppConfig.GALAKSIO_SERVER + "api/histories/" + extra + "/contents",
                    'dataset-details': myAppConfig.GALAKSIO_SERVER + "api/histories/" + extra[0] + "/contents/" + extra[1],
                    'dataset-collection-create': myAppConfig.GALAKSIO_SERVER + "api/dataset_collections/" + extra,
                    'dataset-collection-details': myAppConfig.GALAKSIO_SERVER + "api/histories/" + extra[0] + "/contents/dataset_collections/" + extra[1],
                    'history-list': myAppConfig.GALAKSIO_SERVER + "api/histories/" + extra,
                    'history-create': myAppConfig.GALAKSIO_SERVER + "api/histories/" + extra,
                    'history-export': myAppConfig.GALAKSIO_SERVER + "api/histories/" + extra + "/exports/",
                    'dataset-upload': myAppConfig.GALAKSIO_SERVER + "api/upload/",
                    'setting-list': myAppConfig.GALAKSIO_SERVER + "admin/list-settings",
                    'setting-update': myAppConfig.GALAKSIO_SERVER + "admin/update-settings",
                    'check-is-admin': myAppConfig.GALAKSIO_SERVER + "admin/is-admin",
                    'get-local-galaxy-url': myAppConfig.GALAKSIO_SERVER + "admin/local-galaxy-url",
                    'send-error-report': myAppConfig.GALAKSIO_SERVER + "admin/send-error-report"
                };
                return paths[service] || "";
            };
            
            $rootScope.getHttpRequestConfig = function(method, service, options) {
                options = options || {};
                options.params = options.params || {};
                
                if (Cookies.get("galaksiosession")) {
                    options.params = angular.merge(options.params, {
                        "key": window.atob(Cookies.get("galaksiosession"))
                    });
                }
                
                if (options.urlEncodedRequest === true) {
                    options.transformRequest = function(obj) {
                        var str = [];
                        for (var p in obj) {
                            str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
                        }
                        return str.join("&");
                    };
                }
                
                return {
                    method: method,
                    headers: options.headers,
                    url: $rootScope.getRequestPath(service, options.extra),
                    params: options.params,
                    data: options.data,
                    withCredentials: options.withCredentials === true,
                    transformRequest: options.transformRequest,
                    timeout: myAppConfig.API_TIMEOUT
                };
            };
            
            // State change handling
            $rootScope.$on('$stateChangeStart', function(event, toState, toParams) {
                var requireLogin = toState.data.requireLogin;
                
                if (requireLogin && !isAuthenticated()) {
                    event.preventDefault();
                    Cookies.remove('galaksiosession');
                    $state.go('signin');
                    showToast('warning', 'Authentication Required', 'Please sign in to access this page.');
                }
            });
            
            $rootScope.$on('$stateChangeSuccess', function(event, toState) {
                vm.currentPage = toState.name;
                updatePageTitle(toState.name);
                
                // Load page-specific data
                loadPageData(toState.name);
            });
            
            // Load page-specific data
            function loadPageData(pageName) {
                switch(pageName) {
                    case 'home':
                        loadHomeData();
                        break;
                    case 'workflows':
                        // Workflows controller will handle this
                        break;
                    case 'histories':
                        // Histories controller will handle this
                        break;
                }
            }
            
            // Load home page data
            function loadHomeData() {
                // Load stats
                $http($rootScope.getHttpRequestConfig("GET", "user-info", "current"))
                    .then(function(response) {
                        vm.stats = response.data.stats || {};
                    })
                    .catch(function(error) {
                        console.error('Failed to load user stats:', error);
                    });
                
                // Load recent workflows
                $http($rootScope.getHttpRequestConfig("GET", "workflow-list"))
                    .then(function(response) {
                        vm.recentWorkflows = (response.data || []).slice(0, 5);
                    })
                    .catch(function(error) {
                        console.error('Failed to load recent workflows:', error);
                    });
                
                // Load system status
                loadSystemStatus();
            }
            
            // Load system status
            function loadSystemStatus() {
                $http($rootScope.getHttpRequestConfig("GET", "get-local-galaxy-url", {
                    headers: {'Content-Type': 'application/json; charset=utf-8'}
                }))
                .then(function(response) {
                    vm.systemStatus = {
                        galaxy: 'online',
                        database: 'connected',
                        storage: Math.floor(Math.random() * 30) + 70, // Mock data
                        lastUpdate: new Date()
                    };
                    $rootScope.GALAXY_SERVER_URL = response.data.GALAXY_SERVER_URL;
                    $rootScope.MAX_CONTENT_LENGTH = response.data.MAX_CONTENT_LENGTH;
                })
                .catch(function(error) {
                    vm.systemStatus = {
                        galaxy: 'offline',
                        database: 'disconnected',
                        storage: 0,
                        lastUpdate: new Date()
                    };
                    console.error('Failed to load system status:', error);
                });
            }
            
            // Home page actions
            vm.showHelp = function() {
                showToast('info', 'Help', 'Help documentation is coming soon!');
            };
            
            vm.runWorkflow = function(workflow) {
                if (workflow && workflow.id) {
                    $state.go('workflowRun', {id: workflow.id});
                }
            };
            
            vm.viewWorkflow = function(workflow) {
                if (workflow && workflow.id) {
                    $state.go('workflowDetail', {id: workflow.id});
                }
            };
            
            vm.uploadData = function() {
                showToast('info', 'Upload Data', 'Data upload feature will be available soon!');
            };
            
            // Initialize system status monitoring
            var statusInterval = $interval(function() {
                if (vm.currentPage === 'home') {
                    loadSystemStatus();
                }
            }, 30000); // Update every 30 seconds
            
            // Cleanup
            $scope.$on('$destroy', function() {
                if (statusInterval) {
                    $interval.cancel(statusInterval);
                }
            });
            
            // Initialize
            if (isAuthenticated()) {
                loadSystemStatus();
            }
            
            // Global error handling
            $rootScope.$on(APP_EVENTS.loginFailed, function() {
                showToast('error', 'Login Failed', 'Invalid username or password.');
            });
            
            $rootScope.$on(APP_EVENTS.logoutSuccess, function() {
                showToast('success', 'Logged Out', 'You have been successfully logged out.');
            });
            
            $rootScope.$on(APP_EVENTS.sessionTimeout, function() {
                showToast('warning', 'Session Timeout', 'Your session has expired. Please sign in again.');
                vm.logout();
            });
            
            // Export functions to scope
            $scope.showToast = showToast;
            $scope.removeToast = removeToast;
        }
    ]);

    // Add this to your app.js routing configuration
angular.module('galaksio').config(['$routeProvider', function($routeProvider) {
    $routeProvider
        .when('/paired-reads', {
            templateUrl: 'app/paired-reads.html',
            controller: 'PairedReadsController',
            resolve: {
                // Add any necessary resolves
            }
        })
        // ... other routes
}]);

// Include the new files in your index.html
<script src="app/paired-reads-service.js"></script>
<script src="app/paired-reads-controller.js"></script>
 
    // Utility functions
    function getPathname() {
        var pathname = window.location.pathname;
        return pathname.substring(0, pathname.lastIndexOf('/') + 1);
    }
})();
