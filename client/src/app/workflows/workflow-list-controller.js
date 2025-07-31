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

    var app = angular.module('workflows.controllers.workflow-list', [
        'ang-dialogs',
        'ui.router'
    ]);

    app.controller('WorkflowListController', [
        '$scope', '$rootScope', '$http', '$state', '$timeout', '$filter', '$dialogs', 'myAppConfig',
        function($scope, $rootScope, $http, $state, $timeout, $filter, $dialogs, myAppConfig) {
            
            var vm = this;
            
            // Initialize scope variables
            $scope.workflows = [];
            $scope.filteredWorkflows = [];
            $scope.isLoading = false;
            $scope.searchQuery = '';
            $scope.currentFilter = 'all';
            $scope.sortBy = 'name';
            $scope.currentPage = 1;
            $scope.itemsPerPage = myAppConfig.ITEMS_PER_PAGE || 12;
            $scope.totalPages = 1;
            $scope.pages = [];
            
            // User favorites (stored in localStorage)
            $scope.favorites = JSON.parse(localStorage.getItem('galaksio_favorites') || '[]');

            //--------------------------------------------------------------------
            // DATA LOADING FUNCTIONS
            //--------------------------------------------------------------------

            /**
             * Load workflows from Galaxy API
             */
            this.loadWorkflows = function() {
                $scope.isLoading = true;
                
                $http($rootScope.getHttpRequestConfig("GET", "workflow-list"))
                .then(
                    function successCallback(response) {
                        $scope.workflows = response.data || [];
                        
                        // Add metadata to workflows
                        $scope.workflows.forEach(function(workflow) {
                            workflow.isFavorite = vm.isFavorite(workflow);
                            workflow.run_count = Math.floor(Math.random() * 100); // Mock data
                            workflow.success_rate = Math.floor(Math.random() * 40) + 60; // Mock data
                            workflow.popularity = Math.floor(Math.random() * 50); // Mock data
                            workflow.tags = vm.generateTags(workflow); // Generate tags
                        });
                        
                        vm.applyFilters();
                        $scope.isLoading = false;
                    },
                    function errorCallback(response) {
                        $scope.isLoading = false;
                        $dialogs.showErrorDialog("Failed to load workflows. Please try again later.");
                        console.error("Error loading workflows:", response.data);
                    }
                );
            };

            /**
             * Refresh workflows list
             */
            this.refreshWorkflows = function() {
                this.loadWorkflows();
            };

            //--------------------------------------------------------------------
            // FILTERING AND SORTING FUNCTIONS
            //--------------------------------------------------------------------

            /**
             * Apply filters and sorting to workflows
             */
            this.applyFilters = function() {
                var filtered = $filter('filter')($scope.workflows, $scope.searchQuery);
                
                // Apply category filter
                switch ($scope.currentFilter) {
                    case 'recent':
                        filtered = $filter('orderBy')(filtered, 'create_time', true);
                        filtered = filtered.slice(0, 20); // Last 20 workflows
                        break;
                    case 'popular':
                        filtered = $filter('orderBy')(filtered, 'popularity', true);
                        break;
                    case 'favorites':
                        filtered = filtered.filter(function(workflow) {
                            return vm.isFavorite(workflow);
                        });
                        break;
                    default:
                        // All workflows - no additional filtering
                        break;
                }
                
                // Apply sorting
                switch ($scope.sortBy) {
                    case 'name':
                        filtered = $filter('orderBy')(filtered, 'name');
                        break;
                    case 'date':
                        filtered = $filter('orderBy')(filtered, 'create_time', true);
                        break;
                    case 'popularity':
                        filtered = $filter('orderBy')(filtered, 'popularity', true);
                        break;
                }
                
                $scope.filteredWorkflows = filtered;
                vm.updatePagination();
            };

            /**
             * Set current filter
             */
            this.setFilter = function(filter) {
                $scope.currentFilter = filter;
                vm.applyFilters();
            };

            //--------------------------------------------------------------------
            // PAGINATION FUNCTIONS
            //--------------------------------------------------------------------

            /**
             * Update pagination
             */
            this.updatePagination = function() {
                $scope.totalPages = Math.ceil($scope.filteredWorkflows.length / $scope.itemsPerPage);
                $scope.pages = [];
                
                for (var i = 1; i <= $scope.totalPages; i++) {
                    $scope.pages.push(i);
                }
                
                // Reset to first page if current page is out of bounds
                if ($scope.currentPage > $scope.totalPages) {
                    $scope.currentPage = 1;
                }
            };

            /**
             * Go to specific page
             */
            this.goToPage = function(page) {
                if (page >= 1 && page <= $scope.totalPages) {
                    $scope.currentPage = page;
                }
            };

            /**
             * Go to previous page
             */
            this.previousPage = function() {
                if ($scope.currentPage > 1) {
                    $scope.currentPage--;
                }
            };

            /**
             * Go to next page
             */
            this.nextPage = function() {
                if ($scope.currentPage < $scope.totalPages) {
                    $scope.currentPage++;
                }
            };

            //--------------------------------------------------------------------
            // WORKFLOW ACTIONS
            //--------------------------------------------------------------------

            /**
             * Run a workflow
             */
            this.runWorkflow = function(workflow) {
                if (workflow && workflow.id) {
                    $state.go('workflowRun', {id: workflow.id});
                }
            };

            /**
             * View workflow details
             */
            this.viewWorkflow = function(workflow) {
                if (workflow && workflow.id) {
                    $state.go('workflowDetail', {id: workflow.id});
                }
            };

            /**
             * Toggle workflow favorite status
             */
            this.toggleFavorite = function(workflow) {
                if (vm.isFavorite(workflow)) {
                    vm.removeFromFavorites(workflow);
                } else {
                    vm.addToFavorites(workflow);
                }
            };

            /**
             * Check if workflow is in favorites
             */
            this.isFavorite = function(workflow) {
                return $scope.favorites.indexOf(workflow.id) !== -1;
            };

            /**
             * Add workflow to favorites
             */
            this.addToFavorites = function(workflow) {
                if (!$scope.favorites.includes(workflow.id)) {
                    $scope.favorites.push(workflow.id);
                    localStorage.setItem('galaksio_favorites', JSON.stringify($scope.favorites));
                    workflow.isFavorite = true;
                }
            };

            /**
             * Remove workflow from favorites
             */
            this.removeFromFavorites = function(workflow) {
                var index = $scope.favorites.indexOf(workflow.id);
                if (index !== -1) {
                    $scope.favorites.splice(index, 1);
                    localStorage.setItem('galaksio_favorites', JSON.stringify($scope.favorites));
                    workflow.isFavorite = false;
                }
            };

            //--------------------------------------------------------------------
            // UTILITY FUNCTIONS
            //--------------------------------------------------------------------

            /**
             * Generate tags for workflow based on name and description
             */
            this.generateTags = function(workflow) {
                var tags = [];
                var text = (workflow.name + ' ' + (workflow.description || '')).toLowerCase();
                
                // Common bioinformatics tags
                var commonTags = [
                    'rna-seq', 'dna-seq', 'alignment', 'variant', 'annotation', 
                    'quality', 'assembly', 'phylogeny', 'expression', 'analysis'
                ];
                
                commonTags.forEach(function(tag) {
                    if (text.includes(tag)) {
                        tags.push(tag);
                    }
                });
                
                return tags.slice(0, 3); // Limit to 3 tags
            };

            /**
             * Get paginated workflows
             */
            this.getPaginatedWorkflows = function() {
                var start = ($scope.currentPage - 1) * $scope.itemsPerPage;
                var end = start + $scope.itemsPerPage;
                return $scope.filteredWorkflows.slice(start, end);
            };

            //--------------------------------------------------------------------
            // WATCHERS
            //--------------------------------------------------------------------

            // Watch for search query changes
            $scope.$watch('searchQuery', function() {
                vm.applyFilters();
            });

            // Watch for sort changes
            $scope.$watch('sortBy', function() {
                vm.applyFilters();
            });

            //--------------------------------------------------------------------
            // INITIALIZATION
            //--------------------------------------------------------------------

            // Load workflows on initialization
            this.loadWorkflows();
        }
    ]);

    // Add filter to controller scope
    app.filter('pagination', function() {
        return function(input, start) {
            if (!input || !input.length) return [];
            start = +start;
            return input.slice(start);
        };
    });
})();
