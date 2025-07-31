/**
 * Compatibility Report Controller for Galaksio
 * Handles Galaxy API compatibility reporting and monitoring.
 */

angular.module('galaksio').controller('CompatibilityReportController', [
    '$scope', '$http', '$timeout', '$interval', 'ToastService', 'LoadingService',
    function($scope, $http, $timeout, $interval, ToastService, LoadingService) {
        
        $scope.compatibilityReport = {};
        $scope.loading = false;
        $scope.autoRefresh = false;
        $scope.refreshInterval = null;
        $scope.lastRefreshTime = null;
        $scope.connectionStatus = 'unknown';
        
        // Initialize controller
        $scope.init = function() {
            $scope.loadCompatibilityReport();
            $scope.startAutoRefresh();
        };
        
        // Load compatibility report
        $scope.loadCompatibilityReport = function() {
            $scope.loading = true;
            LoadingService.show('Checking Galaxy compatibility...');
            
            $http.post('/api/get_compatibility_report')
                .then(function(response) {
                    if (response.data.success) {
                        $scope.compatibilityReport = response.data.compatibility_report;
                        $scope.connectionStatus = 'connected';
                        $scope.lastRefreshTime = new Date();
                        
                        ToastService.success('Compatibility report updated');
                    } else {
                        $scope.connectionStatus = 'error';
                        ToastService.error('Failed to load compatibility report: ' + response.data.error);
                    }
                })
                .catch(function(error) {
                    $scope.connectionStatus = 'disconnected';
                    ToastService.error('Error connecting to Galaxy: ' + error.message);
                })
                .finally(function() {
                    $scope.loading = false;
                    LoadingService.hide();
                });
        };
        
        // Start auto refresh
        $scope.startAutoRefresh = function() {
            if ($scope.refreshInterval) {
                $interval.cancel($scope.refreshInterval);
            }
            
            $scope.refreshInterval = $interval(function() {
                if ($scope.autoRefresh) {
                    $scope.loadCompatibilityReport();
                }
            }, 30000); // Refresh every 30 seconds
        };
        
        // Toggle auto refresh
        $scope.toggleAutoRefresh = function() {
            $scope.autoRefresh = !$scope.autoRefresh;
            if ($scope.autoRefresh) {
                ToastService.info('Auto refresh enabled');
            } else {
                ToastService.info('Auto refresh disabled');
            }
        };
        
        // Get status class
        $scope.getStatusClass = function(isCompatible) {
            return isCompatible ? 'text-success' : 'text-danger';
        };
        
        // Get status icon
        $scope.getStatusIcon = function(isCompatible) {
            return isCompatible ? 'fas fa-check-circle' : 'fas fa-times-circle';
        };
        
        // Get connection status class
        $scope.getConnectionStatusClass = function() {
            switch ($scope.connectionStatus) {
                case 'connected':
                    return 'text-success';
                case 'disconnected':
                    return 'text-danger';
                case 'error':
                    return 'text-warning';
                default:
                    return 'text-muted';
            }
        };
        
        // Get connection status icon
        $scope.getConnectionStatusIcon = function() {
            switch ($scope.connectionStatus) {
                case 'connected':
                    return 'fas fa-wifi';
                case 'disconnected':
                    return 'fas fa-wifi-slash';
                case 'error':
                    return 'fas fa-exclamation-triangle';
                default:
                    return 'fas fa-question-circle';
            }
        };
        
        // Get connection status text
        $scope.getConnectionStatusText = function() {
            switch ($scope.connectionStatus) {
                case 'connected':
                    return 'Connected';
                case 'disconnected':
                    return 'Disconnected';
                case 'error':
                    return 'Error';
                default:
                    return 'Unknown';
            }
        };
        
        // Test connection
        $scope.testConnection = function() {
            $scope.loading = true;
            LoadingService.show('Testing Galaxy connection...');
            
            $http.post('/api/test_connection', {
                galaxy_url: $scope.compatibilityReport.galaxy_version ? 
                    'https://usegalaxy.org' : 'https://usegalaxy.org'
            })
            .then(function(response) {
                if (response.data.success) {
                    ToastService.success('Connection test successful');
                    $scope.loadCompatibilityReport();
                } else {
                    ToastService.error('Connection test failed: ' + response.data.error);
                }
            })
            .catch(function(error) {
                ToastService.error('Connection test error: ' + error.message);
            })
            .finally(function() {
                $scope.loading = false;
                LoadingService.hide();
            });
        };
        
        // Export compatibility report
        $scope.exportReport = function() {
            const reportData = {
                compatibility_report: $scope.compatibilityReport,
                export_time: new Date().toISOString(),
                connection_status: $scope.connectionStatus,
                last_refresh: $scope.lastRefreshTime
            };
            
            const blob = new Blob([JSON.stringify(reportData, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `galaxy-compatibility-report-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            ToastService.success('Compatibility report exported');
        };
        
        // Format timestamp
        $scope.formatTimestamp = function(timestamp) {
            if (!timestamp) return 'Never';
            return new Date(timestamp).toLocaleString();
        };
        
        // Get version badge class
        $scope.getVersionBadgeClass = function(version) {
            if (!version) return 'bg-secondary';
            if (version.startsWith('25.')) return 'bg-success';
            if (version.startsWith('24.')) return 'bg-warning';
            return 'bg-danger';
        };
        
        // Check if feature is supported
        $scope.isFeatureSupported = function(feature) {
            return $scope.compatibilityReport.supported_features && 
                   $scope.compatibilityReport.supported_features.includes(feature);
        };
        
        // Get feature status icon
        $scope.getFeatureStatusIcon = function(feature) {
            return $scope.isFeatureSupported(feature) ? 
                'fas fa-check text-success' : 'fas fa-times text-danger';
        };
        
        // Refresh manually
        $scope.refresh = function() {
            $scope.loadCompatibilityReport();
        };
        
        // Cleanup on destroy
        $scope.$on('$destroy', function() {
            if ($scope.refreshInterval) {
                $interval.cancel($scope.refreshInterval);
            }
        });
        
        // Initialize
        $scope.init();
    }
]);
