/**
 * Paired Reads Controller for Galaksio
 * Manages the paired-end reads detection and management interface
 */

angular.module('b3galaxyApp').controller('PairedReadsController', [
    '$scope', '$timeout', '$interval', 'PairedReadsService', 'HistoryService', 'NotificationService',
    function($scope, $timeout, $interval, PairedReadsService, HistoryService, NotificationService) {
        
        $scope.isLoading = false;
        $scope.selectedHistory = null;
        $scope.pairedReads = null;
        $scope.supportedPatterns = [];
        $scope.autoPairing = false;
        $scope.batchCreating = false;
        $scope.selectedPairs = [];
        $scope.selectAll = false;
        $scope.filters = {
            confidence: 'all',
            pairType: 'all',
            collectionStatus: 'all',
            searchTerm: ''
        };
        $scope.progress = null;
        $scope.retryCount = 0;
        
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
            }).catch(function(error) {
                NotificationService.error('Network error loading histories: ' + error.message);
            });
        };
        
        // Load supported paired read patterns
        $scope.loadSupportedPatterns = function() {
            PairedReadsService.getPairedReadPatterns().then(function(response) {
                if (response.success) {
                    $scope.supportedPatterns = response.patterns;
                    $scope.supportedExtensions = response.supported_extensions;
                }
            }).catch(function(error) {
                console.warn('Could not load paired read patterns:', error);
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
            $scope.retryCount = 0;
            
            PairedReadsService.detectPairedReads($scope.selectedHistory.id)
                .then(function(response) {
                    $scope.isLoading = false;
                    
                    if (response.success) {
                        $scope.pairedReads = response;
                        NotificationService.success(
                            `Detected ${response.total_pairs} paired groups and ${response.total_unpaired} unpaired files`
                        );
                        
                        // Show compatibility warnings if any
                        if (response.compatibility_report && !response.compatibility_report.is_compatible) {
                            $scope.showCompatibilityWarnings(response.compatibility_report);
                        }
                    } else {
                        NotificationService.error('Failed to detect paired reads: ' + response.error);
                        $scope.scheduleRetry();
                    }
                })
                .catch(function(error) {
                    $scope.isLoading = false;
                    console.error('Error detecting paired reads:', error);
                    NotificationService.error('Network error occurred while detecting paired reads');
                    $scope.scheduleRetry();
                });
        };
        
        // Schedule retry with exponential backoff
        $scope.scheduleRetry = function() {
            $scope.retryCount++;
            if ($scope.retryCount <= 3) {
                var delay = Math.pow(2, $scope.retryCount) * 1000; // 2s, 4s, 8s
                NotificationService.warning(`Retrying in ${delay/1000} seconds...`);
                $timeout(function() {
                    $scope.detectPairedReads();
                }, delay);
            }
        };
        
        // Show compatibility warnings
        $scope.showCompatibilityWarnings = function(compatibilityReport) {
            if (compatibilityReport.issues_count > 0) {
                var warningMessage = 'Galaxy compatibility issues detected: ' + 
                    compatibilityReport.issues_count + ' issues found. Some features may not work properly.';
                NotificationService.warning(warningMessage, 10000); // Show for 10 seconds
            }
        };
        
        // Auto-pair all reads
        $scope.autoPairAllReads = function() {
            if (!$scope.selectedHistory) {
                NotificationService.warning('Please select a history first');
                return;
            }
            
            $scope.autoPairing = true;
            $scope.progress = {
                current: 0,
                total: 100,
                stage: 'Initializing...'
            };
            
            // Simulate progress updates
            $scope.progressInterval = $interval(function() {
                if ($scope.progress.current < $scope.progress.total) {
                    $scope.progress.current += Math.random() * 10;
                    if ($scope.progress.current > 90) {
                        $scope.progress.stage = 'Finalizing...';
                    } else if ($scope.progress.current > 60) {
                        $scope.progress.stage = 'Creating collections...';
                    } else if ($scope.progress.current > 30) {
                        $scope.progress.stage = 'Detecting pairs...';
                    }
                }
            }, 500);
            
            PairedReadsService.autoPairAllReads($scope.selectedHistory.id, true)
                .then(function(response) {
                    $interval.cancel($scope.progressInterval);
                    $scope.autoPairing = false;
                    $scope.progress.current = 100;
                    $scope.progress.stage = 'Complete';
                    
                    if (response.success) {
                        $scope.pairedReads = response;
                        const summary = response.summary;
                        
                        NotificationService.success(
                            `Auto-pairing completed: ${summary.high_confidence_pairs} high-confidence pairs, ` +
                            `${summary.collections_created} collections created`
                        );
                        
                        // Show compatibility report if issues found
                        if (response.compatibility_report && !response.compatibility_report.is_compatible) {
                            $scope.showCompatibilityWarnings(response.compatibility_report);
                        }
                    } else {
                        NotificationService.error('Auto-pairing failed: ' + response.error);
                    }
                    
                    // Reset progress after delay
                    $timeout(function() {
                        $scope.progress = null;
                    }, 3000);
                })
                .catch(function(error) {
                    $interval.cancel($scope.progressInterval);
                    $scope.autoPairing = false;
                    $scope.progress = null;
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
            
            PairedReadsService.createPairedCollection($scope.selectedHistory.id, pairedGroup)
                .then(function(response) {
                    pairedGroup.creating = false;
                    
                    if (response.success) {
                        pairedGroup.collectionCreated = true;
                        pairedGroup.collectionId = response.collection_id;
                        NotificationService.success('Paired collection created: ' + response.collection_name);
                    } else {
                        NotificationService.error('Failed to create paired collection: ' + response.error);
                    }
                })
                .catch(function(error) {
                    pairedGroup.creating = false;
                    NotificationService.error('Error creating paired collection: ' + error.message);
                });
        };
        
        // Batch operations
        $scope.toggleSelectAll = function() {
            $scope.selectedPairs = $scope.selectAll ? 
                $scope.getFilteredPairs().map(g => g.group_id) : [];
        };
        
        $scope.togglePairSelection = function(groupId) {
            const index = $scope.selectedPairs.indexOf(groupId);
            if (index > -1) {
                $scope.selectedPairs.splice(index, 1);
            } else {
                $scope.selectedPairs.push(groupId);
            }
            $scope.selectAll = $scope.selectedPairs.length === $scope.getFilteredPairs().length;
        };
        
        $scope.batchCreateCollections = function() {
            if ($scope.selectedPairs.length === 0) {
                NotificationService.warning('Please select pairs to create collections');
                return;
            }
            
            $scope.batchCreating = true;
            let completed = 0;
            let errors = 0;
            
            const createNext = function() {
                if ($scope.selectedPairs.length === 0) {
                    $scope.batchCreating = false;
                    NotificationService.success(
                        `Batch creation completed: ${completed} collections created, ${errors} errors`
                    );
                    return;
                }
                
                const groupId = $scope.selectedPairs.shift();
                const group = $scope.pairedReads.paired_groups.find(g => g.group_id === groupId);
                
                if (group && !group.collectionCreated) {
                    PairedReadsService.createPairedCollection($scope.selectedHistory.id, group)
                        .then(function(response) {
                            if (response.success) {
                                group.collectionCreated = true;
                                group.collectionId = response.collection_id;
                                completed++;
                            } else {
                                errors++;
                            }
                            createNext();
                        })
                        .catch(function() {
                            errors++;
                            createNext();
                        });
                } else {
                    createNext();
                }
            };
            
            createNext();
        };
        
        // Filtering and search
        $scope.getFilteredPairs = function() {
            if (!$scope.pairedReads || !$scope.pairedReads.paired_groups) {
                return [];
            }
            
            return $scope.pairedReads.paired_groups.filter(function(group) {
                // Confidence filter
                if ($scope.filters.confidence === 'high' && group.confidence < 0.7) return false;
                if ($scope.filters.confidence === 'medium' && (group.confidence < 0.6 || group.confidence >= 0.7)) return false;
                if ($scope.filters.confidence === 'low' && group.confidence >= 0.6) return false;
                
                // Pair type filter
                if ($scope.filters.pairType !== 'all' && group.pair_type !== $scope.filters.pairType) return false;
                
                // Collection status filter
                if ($scope.filters.collectionStatus === 'created' && !group.collectionCreated) return false;
                if ($scope.filters.collectionStatus === 'uncreated' && group.collectionCreated) return false;
                
                // Search term filter
                if ($scope.filters.searchTerm) {
                    const searchLower = $scope.filters.searchTerm.toLowerCase();
                    const nameMatch = group.suggested_name.toLowerCase().includes(searchLower);
                    const fileMatch = group.files.some(function(file) {
                        return file.name.toLowerCase().includes(searchLower);
                    });
                    if (!nameMatch && !fileMatch) return false;
                }
                
                return true;
            });
        };
        
        // Export results
        $scope.exportResults = function() {
            const filteredPairs = $scope.getFilteredPairs();
            const exportData = {
                timestamp: new Date().toISOString(),
                history_id: $scope.selectedHistory.id,
                history_name: $scope.selectedHistory.name,
                total_pairs: filteredPairs.length,
                filters: $scope.filters,
                pairs: filteredPairs.map(function(group) {
                    return {
                        group_id: group.group_id,
                        suggested_name: group.suggested_name,
                        pair_type: group.pair_type,
                        confidence: group.confidence,
                        files: group.files.map(function(f) { 
                            return { 
                                id: f.id, 
                                name: f.name, 
                                size: f.file_size,
                                data_type: f.data_type
                            }; 
                        }),
                        collection_created: group.collectionCreated,
                        collection_id: group.collectionId
                    };
                })
            };
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `paired-reads-analysis-${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
            
            NotificationService.success('Results exported successfully');
        };
        
        // Utility functions
        $scope.formatFileSize = function(bytes) {
            return PairedReadsService.formatFileSize(bytes);
        };
        
        $scope.getConfidenceLevel = function(confidence) {
            return PairedReadsService.getConfidenceLevel(confidence);
        };
        
        $scope.getPairTypeDescription = function(pairType) {
            return PairedReadsService.getPairTypeDescription(pairType);
        };
        
        $scope.canCreateCollection = function(pairedGroup) {
            return pairedGroup && 
                   pairedGroup.confidence >= 0.7 && 
                   !pairedGroup.collectionCreated && 
                   !pairedGroup.creating;
        };
        
        $scope.getConfidenceColor = function(confidence) {
            if (confidence >= 0.8) return 'success';
            if (confidence >= 0.6) return 'warning';
            return 'danger';
        };
        
        // Watch for filter changes
        $scope.$watch('filters', function() {
            $scope.selectAll = false;
            $scope.selectedPairs = [];
        }, true);
        
        // Initialize controller
        $scope.init();
    }
]);
