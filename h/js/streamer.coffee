sock = new SockJS('http://0.0.0.0:5001/streamer')
  
angular.module('h.streamer',[])
  .controller('StreamerCtrl',
  ($scope, $element) ->
    $scope.annotations = []    

    #sock.onopen = ->
    #sock.onclose = ->
    sock.onmessage = (msg) =>
      console.log msg.data
      $scope.$apply =>
        $scope.annotations.push msg.data
)

