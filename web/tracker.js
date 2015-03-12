'use strict';

angular.module('siftracker', ['ngRoute', 'ngResource'])
    .factory('Ranking', ['$resource',
            function($resource) {
                return $resource( 'ranking/:eventId', {},
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
            $scope.event_id = $routeParams.event_id || 19
            $scope.ranking = Ranking.query({eventId:$scope.event_id,limit:1000});
            $scope.orderProp = 'rank';
        }])
    .controller('HistoryUserCtrl', ['$scope', '$routeParams', 'HistoryUser',
        function($scope, $routeParams, HistoryUser) {
            $scope.history = HistoryUser.query({
                eventId: $routeParams.eventId,
                userId: $routeParams.userId});
            $scope.orderProp = 'step';
        }]);

angular.module('siftracker')
    .config(['$routeProvider', function($routeProvider) {
        $routeProvider.
            when('/ranking', {
                templateUrl: 'partials/ranking-list.html',
                controller: 'RankingCtrl'
            }).
            when('/history_user/:eventId/:userId', {
                templateUrl: 'partials/history-user.html',
                controller: 'HistoryUserCtrl'
            }).
            otherwise({
                redirectTo: '/ranking'
            });
    }]);
