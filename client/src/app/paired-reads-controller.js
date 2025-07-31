/**
 * Paired Reads Controller for Galaksio
 * Manages the paired-end reads detection and management interface
 */

angular.module('galaksio').controller('PairedReadsController', [
    '$scope', '$timeout', 'PairedReadsService', 'HistoryService', 'NotificationService',
    function($scope, $timeout, PairedReadsService, HistoryService, NotificationService) {
        
        $scope.isLoading = false;
        $scope.selectedHistory = null;
        $scope.pairedReads = null;
        $scope.supportedPatterns = [];
        $scope.autoPairing = false;
        
        // Initialize
        $scope.init = function() {
            $scope.loadHistories();
            $scope.loadSupportedPatterns();
        };
        
        // Load available histories
        $scope.loadHistories = function() {
            HistoryService.getHistories().then(function(response) {
                if (response.success) {
                    $scope.histories = response.histories;
                } else {
                    NotificationService.error('Failed to load histories: ' + response.error);
                }
            });
        };
        
        // Load supported paired read patterns
        $scope.loadSupportedPatterns = function() {
            PairedReadsService.getPairedReadPatterns().then(function(response) {
                if (response.success) {
                    $scope.supportedPatterns = response.patterns;
                    $scope.supportedExtensions = response.supported_extensions;
                }
            });
        };
        
        // Detect paired reads in selected history
        $scope.detectPairedReads = function() {
            if (!$scope.selectedHistory) {
                NotificationService.warning('Please select a history first');
                return;
            }
            
            $scope.isLoading = true;
            $scope.pairedReads = null;
            
            PairedReadsService.detectPairedReads($scope.selectedHistory.id).then(function(response) {
                $scope.isLoading = false;
                
                if (response.success) {
                    $scope.pairedReads = response;
                    NotificationService.success(
                        `Detected ${response.total_pairs} paired groups and ${response.total_unpaired} unpaired files`
                    );
                } else {
                    NotificationService.error('Failed to detect paired reads: ' + response.error);
                }
            }).catch(function(error) {
                $scope.isLoading = false;
                NotificationService.error('Error detecting paired reads: ' + error.message);
            });
        };
        
        // Auto-pair all reads
        $scope.autoPairAllReads = function() {
            if (!$scope.selectedHistory) {
                NotificationService.warning('Please select a history first');
                return;
            }
            
            $scope.autoPairing = true;
            
            PairedReadsService.autoPairAllReads($scope.selectedHistory.id, true).then(function(response) {
                $scope.autoPairing = false;
                
                if (response.success) {
                    $scope.pairedReads = response;
                    const summary = response.summary;
                    
                    NotificationService.success(
                        `Auto-pairing completed: ${summary.high_confidence_pairs} high-confidence pairs, ` +
                        `${summary.collections_created} collections created`
                    );
                } else {
                    NotificationService.error('Auto-pairing failed: ' + response.error);
                }
            }).catch(function(error) {
                $scope.autoPairing = false;
                NotificationService.error('Error auto-pairing reads: ' + error.message);
            });
        };
        
        // Create paired collection
        $scope.createPairedCollection = function(pairedGroup) {
            if (!$scope.selectedHistory) {
                NotificationService.warning('Please select a history first');
                return;
            }
            
            pairedGroup.creating = true;
            
            PairedReadsService.createPairedCollection($scope.selectedHistory.id, pairedGroup).then(function(response) {
                pairedGroup.creating = false;
                
                if (response.success) {
                    pairedGroup.collectionCreated = true;
                    pairedGroup.collectionId = response.collection_id;
                    NotificationService.success('Paired collection created: ' + response.collection_name);
                } else {
                    NotificationService.error('Failed to create paired collection: ' + response.error);
                }
            }).catch(function(error) {
                pairedGroup.creating = false;
                NotificationService.error('Error creating paired collection: ' + error.message);
            });
        };
        
        // Format file size
        $scope.formatFileSize = function(bytes) {
            return PairedReadsService.formatFileSize(bytes);
        };
        
        // Get confidence level
        $scope.getConfidenceLevel = function(confidence) {
            return PairedReadsService.getConfidenceLevel(confidence);
        };
        
        // Get pair type description
        $scope.getPairTypeDescription = function(pairType) {
            return PairedReadsService.getPairTypeDescription(pairType);
        };
        
        // Check if paired group can be made into collection
        $scope.canCreateCollection = function(pairedGroup) {
            return pairedGroup && 
                   pairedGroup.confidence >= 0.7 && 
                   !pairedGroup.collectionCreated && 
                   !pairedGroup.creating;
        };
        
        // Initialize controller
        $scope.init();
    }
]);
