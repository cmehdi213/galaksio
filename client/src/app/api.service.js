(function() {
    'use strict';

    angular.module('b3galaxyApp')
        .factory('ApiService', ['myAppConfig', function(myAppConfig) {
            var getRequestPath = function(service, extra) {
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

            return {
                getRequestPath: getRequestPath
            };
        }]);
})();
