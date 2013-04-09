get_quote = (annotation) ->
  if not 'target' in annotation then return ''
  quote = ''
  for target in annotation['target']
    for selector in target['selector']
        if selector['type'] is 'TextQuoteSelector' 
            quote = quote + selector['exact'] + ' '

  quote

sock = new SockJS('http://0.0.0.0:5001/streamer')
  
angular.module('h.streamer',['h.filters'])
  .controller('StreamerCtrl',
  ($scope, $element) ->
    $scope.annotations = []    

    #sock.onopen = ->
    #sock.onclose = ->
    sock.onmessage = (msg) =>
      $scope.$apply =>
        console.log msg.data
        msg.data['quote'] = get_quote msg.data
        $scope.annotations.push msg.data
  )


