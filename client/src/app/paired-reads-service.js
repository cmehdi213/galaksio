/**
 * Paired Reads Service for Galaksio
 * Handles automatic detection and management of paired-end sequencing reads
 */

angular.module('b3galaxyApp').factory('PairedReadsService', ['$http', '$q', function($http, $q) {
    return {
        /**
         * Detect paired-end reads in a Galaxy history
         */
        detectPairedReads: function(historyId) {
            return $http.post('/api/detect_paired_reads', {
                history_id: historyId
            }).then(function(response) {
                return response.data;
            }).catch(function(error) {
                return $q.reject(error);
            });
        },
        
        /**
         * Create a paired collection from detected paired reads
         */
        createPairedCollection: function(historyId, pairedGroup) {
            return $http.post('/api/create_paired_collection', {
                history_id: historyId,
                paired_group: pairedGroup
            }).then(function(response) {
                return response.data;
            }).catch(function(error) {
                return $q.reject(error);
            });
        },
        
        /**
         * Automatically detect and pair all reads in a history
         */
        autoPairAllReads: function(historyId, createCollections) {
            createCollections = createCollections !== false;
            
            return $http.post('/api/auto_pair_all_reads', {
                history_id: historyId,
                create_collections: createCollections
            }).then(function(response) {
                return response.data;
            }).catch(function(error) {
                return $q.reject(error);
            });
        },
        
        /**
         * Get supported paired read patterns
         */
        getPairedReadPatterns: function() {
            return $http.get('/api/get_paired_read_patterns')
                .then(function(response) {
                    return response.data;
                }).catch(function(error) {
                    return $q.reject(error);
                });
        },
        
        /**
         * Format file size for display
         */
        formatFileSize: function(bytes) {
            if (bytes === 0) return '0 Bytes';
            
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },
        
        /**
         * Get confidence level description
         */
        getConfidenceLevel: function(confidence) {
            if (confidence >= 0.8) return { level: 'high', class: 'success', text: 'High' };
            if (confidence >= 0.6) return { level: 'medium', class: 'warning', text: 'Medium' };
            return { level: 'low', class: 'danger', text: 'Low' };
        },
        
        /**
         * Get pair type description
         */
        getPairTypeDescription: function(pairType) {
            const types = {
                'illumina_r1_r2': 'Illumina R1/R2',
                'illumina_r2_r1': 'Illumina R2/R1',
                'illumina_1_2': 'Illumina 1/2',
                'illumina_2_1': 'Illumina 2/1',
                'forward_reverse': 'Forward/Reverse',
                'reverse_forward': 'Reverse/Forward',
                'unknown': 'Unknown'
            };
            
            return types[pairType] || 'Unknown';
        }
    };
}]);
