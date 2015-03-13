'use strict';

angular.module('siftracker', ['ngRoute', 'ngResource'])
    .factory('Ranking', ['$resource',
            function($resource) {
                return $resource( 'ranking/:eventId', {},
                    {query: {method:'GET', params:{},isArray: true}});
            }])
    .factory('Cutoff', ['$resource',
            function($resource) {
                return $resource( 'cutoff/:eventId', {},
                    {query: {method:'GET', params:{},isArray: true}});
            }])
    .factory('HistoryUser', ['$resource',
            function($resource) {
                return $resource( 'history_user/:eventId/:userId', {},
                    {query: {method:'GET', params:{},isArray: true}});
            }]);

angular.module('siftracker')
    .controller('RankingCtrl', ['$scope', '$routeParams', 'Ranking',
        function($scope, $routeParams, Ranking) {
            $scope.event_id = $routeParams.eventId || 21;
            $scope.page = parseInt($routeParams.page) || 0;
            $scope.next_page = $scope.page + 1;
            $scope.prev_page = $scope.page - 1;
            $scope.ranking = Ranking.query({
                eventId: $scope.event_id,
                limit: 500,
                page: $scope.page
            });
            $scope.orderProp = 'rank';
        }])
    .controller('CutoffCtrl', ['$scope', '$routeParams', 'Cutoff',
        function($scope, $routeParams, Cutoff) {
            $scope.event_id = $routeParams.eventId || 21
            $scope.cutoffs = Cutoff.query({eventId: $scope.event_id});
            $scope.orderProp = 'step';
        }])
    .controller('HistoryUserCtrl', ['$scope', '$routeParams', 'HistoryUser',
        function($scope, $routeParams, HistoryUser) {
            $scope.history = HistoryUser.query({
                eventId: $routeParams.eventId,
                userId: $routeParams.userId});
            $scope.orderProp = 'step';
        }])
    .controller('RevisionCtrl', ['$scope', '$http',
        function($scope, $http) {
            $http.get('revision').success(function(data) {
                $scope.revision = data.revision;
            });
        }]);

angular.module('siftracker')
    .config(['$routeProvider', function($routeProvider) {
        $routeProvider.
            when('/ranking', {
                templateUrl: 'partials/ranking-list.html',
                controller: 'RankingCtrl'
            }).
            when('/ranking/:eventId', {
                templateUrl: 'partials/ranking-list.html',
                controller: 'RankingCtrl'
            }).
            when('/ranking/:eventId/:page', {
                templateUrl: 'partials/ranking-list.html',
                controller: 'RankingCtrl'
            }).
            when('/cutoff', {
                templateUrl: 'partials/cutoff-list.html',
                controller: 'CutoffCtrl'
            }).
            when('/cutoff/:eventId', {
                templateUrl: 'partials/cutoff-list.html',
                controller: 'CutoffCtrl'
            }).
            when('/history_user/:eventId/:userId', {
                templateUrl: 'partials/history-user.html',
                controller: 'HistoryUserCtrl'
            }).
            otherwise({
                redirectTo: '/ranking'
            });
    }]);
