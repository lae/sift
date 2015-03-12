'use strict';

angular.module('siftracker', ['ngRoute', 'ngResource'])
    .factory('Ranking', ['$resource',
            function($resource) {
                return $resource( 'ranking/:eventId', {},
                    {query: {method:'GET', params:{},isArray: true}});
            }]);

angular.module('siftracker')
    .controller('RankingCtrl', ['$scope', '$routeParams', 'Ranking',
        function($scope, $routeParams, Ranking) {
            $scope.ranking = Ranking.query({eventId:19,limit:1000});
            $scope.orderProp = 'rank';
        }]);

angular.module('siftracker')
    .config(['$routeProvider', function($routeProvider) {
        $routeProvider.
            when('/ranking', {
                templateUrl: 'partials/ranking-list.html',
                controller: 'RankingCtrl'
            }).
            otherwise({
                redirectTo: '/ranking'
            });
    }]);
