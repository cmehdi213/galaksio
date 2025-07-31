/**
 * Compatibility Report Controller for Galaksio
 * Displays Galaxy API compatibility information and recommendations.
 */

angular.module('galaksio').controller('CompatibilityReportController', [
    '$scope', '$timeout', 'GalaxyService', 'NotificationService',
    function($scope, $timeout, GalaxyService, NotificationService) {
        
        $scope.compatibilityReport = null;
        $scope.isLoading = false;
        $scope.showDetails = false;
        
        // Initialize
        $scope.init = function() {
            $scope.loadCompatibilityReport();
        };
        
        // Load compatibility report
        $scope.loadCompatibilityReport = function() {
            $scope.isLoading = true;
            $scope.compatibilityReport = null;
            
            GalaxyService.getCompatibilityReport().then(function(response) {
                $scope.isLoading = false;
                
                if (response.success) {
                    $scope.compatibilityReport = response.compatibility_report;
                    $scope.analyzeCompatibility();
                } else {
                    NotificationService.error('Failed to load compatibility report: ' + response.error);
                }
            }).catch(function(error) {
                $scope.isLoading = false;
                NotificationService.error('Error loading compatibility report: ' + error.message);
            });
        };
        
        // Analyze compatibility and provide recommendations
        $scope.analyzeCompatibility = function() {
            if (!$scope.compatibilityReport) return;
            
            const report = $scope.compatibilityReport;
            
            // Determine overall status
            if (report.is_compatible) {
                $scope.overallStatus = {
                    level: 'success',
                    icon: 'fas fa-check-circle',
                    message: 'Fully Compatible',
                    description: 'Your Galaxy instance is fully compatible with Galaksio 2'
                };
            } else if (report.is_galaxy_25_plus) {
                $scope.overallStatus = {
                    level: 'warning',
                    icon: 'fas fa-exclamation-triangle',
                    message: 'Partially Compatible',
                    description: 'Galaxy 25.0+ detected with some compatibility issues'
                };
            } else {
                $scope.overallStatus = {
                    level: 'danger',
                    icon: 'fas fa-times-circle',
                    message: 'Compatibility Issues',
                    description: 'Compatibility issues detected that may affect functionality'
                };
            }
            
            // Analyze specific issues
            $scope.analyzeIssues();
        };
        
        // Analyze specific compatibility issues
        $scope.analyzeIssues = function() {
            if (!$scope.compatibilityReport || !$scope.compatibilityReport.compatibility_issues) {
                $scope.issueCategories = [];
                return;
            }
            
            const issues = $scope.compatibilityReport.compatibility_issues;
            $scope.issueCategories = {
                critical: [],
                warning: [],
                info: []
            };
            
            issues.forEach(function(issue) {
                if (issue.includes('failed') || issue.includes('error')) {
                    $scope.issueCategories.critical.push({
                        type: 'critical',
                        message: issue,
                        recommendation: 'This issue may prevent some features from working properly'
                    });
                } else if (issue.includes('warning') || issue.includes('deprecated')) {
                    $scope.issueCategories.warning.push({
                        type: 'warning',
                        message: issue,
                        recommendation: 'This may cause issues in future versions'
                    });
                } else {
                    $scope.issueCategories.info.push({
                        type: 'info',
                        message: issue,
                        recommendation: 'Informational message for reference'
                    });
                }
            });
        };
        
        // Get status class for styling
        $scope.getStatusClass = function(level) {
            const classes = {
                'success': 'text-success',
                'warning': 'text-warning',
                'danger': 'text-danger',
                'info': 'text-info'
            };
            return classes[level] || 'text-secondary';
        };
        
        // Get badge class for issues
        $scope.getIssueBadgeClass = function(type) {
            const classes = {
                'critical': 'bg-danger',
                'warning': 'bg-warning',
                'info': 'bg-info'
            };
            return classes[type] || 'bg-secondary';
        };
        
        // Format version information
        $scope.formatVersionInfo = function() {
            if (!$scope.compatibilityReport) return '';
            
            const report = $scope.compatibilityReport;
            let info = `Galaxy ${report.galaxy_version || 'unknown'}`;
            
            if (report.api_version) {
                info += ` (API ${report.api_version})`;
            }
            
            if (report.is_galaxy_25_plus) {
                info += ' - 25.0+ Compatible';
            }
            
            return info;
        };
        
        // Refresh compatibility report
        $scope.refreshReport = function() {
            $scope.loadCompatibilityReport();
        };
        
        // Toggle detailed view
        $scope.toggleDetails = function() {
            $scope.showDetails = !$scope.showDetails;
        };
        
        // Copy report to clipboard
        $scope.copyReport = function() {
            if (!$scope.compatibilityReport) return;
            
            const reportText = JSON.stringify($scope.compatibilityReport, null, 2);
            
            if (navigator.clipboard) {
                navigator.clipboard.writeText(reportText).then(function() {
                    NotificationService.success('Compatibility report copied to clipboard');
                }).catch(function() {
                    NotificationService.error('Failed to copy report to clipboard');
                });
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = reportText;
                document.body.appendChild(textArea);
                textArea.select();
                
                try {
                    document.execCommand('copy');
                    NotificationService.success('Compatibility report copied to clipboard');
                } catch (err) {
                    NotificationService.error('Failed to copy report to clipboard');
                }
                
                document.body.removeChild(textArea);
            }
        };
        
        // Initialize controller
        $scope.init();
    }
]);
