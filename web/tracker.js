'use strict';

angular.module('siftracker', ['ngRoute', 'ngResource'])
    .factory('Ranking', ['$resource',
            function($resource) {
                return $resource( 'ranking/:eventId', {},
                    {query: {method:'GET', params:{},isArray: true}});
            }])
    .factory('YonChanneru', ['$resource',
            function($resource) {
                return $resource( 'yonchanneru/:eventId', {},
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
            $scope.event_id = $routeParams.eventId || 23;
            $scope.page = parseInt($routeParams.page) || 0;
            $scope.next_page = $scope.page + 1;
            $scope.prev_page = $scope.page - 1;
            $scope.ranking = Ranking.query({
                eventId: $scope.event_id,
                limit: 100,
                page: $scope.page
            });
            $scope.orderProp = 'rank';
        }])
    .controller('YonChanneruCtrl', ['$scope', '$routeParams', 'YonChanneru',
        function($scope, $routeParams, YonChanneru) {
            $scope.event_id = $routeParams.eventId || 23;
            $scope.ranking = YonChanneru.query({
                eventId: $scope.event_id
            });
            $scope.orderProp = 'rank';
        }])
    .controller('CutoffCtrl', ['$scope', '$routeParams', 'Cutoff',
        function($scope, $routeParams, Cutoff) {
            $scope.event_id = $routeParams.eventId || 23
            $scope.cutoffs = Cutoff.query({eventId: $scope.event_id});
            $scope.orderProp = '-step';
        }])
    .controller('HistoryUserCtrl', ['$scope', '$routeParams', 'HistoryUser', '$http',
        function($scope, $routeParams, HistoryUser, $http) {
            $scope.user_id = $routeParams.userId;
            $http.get('history_user_events/' + $scope.user_id).success(function(data) {
                $scope.played_events = data;
            });
            $scope.history = HistoryUser.query({
                eventId: $routeParams.eventId,
                userId: $scope.user_id});
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
            when('/yonchanneru/:eventId', {
                templateUrl: 'partials/yonchanneru-list.html',
                controller: 'YonChanneruCtrl'
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
