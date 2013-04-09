fuzzyTime = (date) ->
  return '' if not date
  delta = Math.round((+new Date - new Date(date)) / 1000)

  minute = 60
  hour = minute * 60
  day = hour * 24
  week = day * 7
  month = day * 30

  if (delta < 30)
    fuzzy = 'moments ago'
  else if (delta < minute)
    fuzzy = delta + ' seconds ago'
   else if (delta < 2 * minute)
    fuzzy = 'a minute ago'
   else if (delta < hour)
    fuzzy = Math.floor(delta / minute) + ' minutes ago'
   else if (Math.floor(delta / hour) == 1)
    fuzzy = '1 hour ago'
   else if (delta < day)
    fuzzy = Math.floor(delta / hour) + ' hours ago'
   else if (delta < day * 2)
    fuzzy = 'yesterday'
   else if (delta < month)
    fuzzy = Math.round(delta / day) + ' days ago'
   else
    fuzzy = new Date(date)


userName = (user) ->
  (user?.match /^acct:([^@]+)/)?[1]

sock = new SockJS('http://0.0.0.0:5001/streamer')
  
angular.module('h.streamer',[])
  .controller('StreamerCtrl',
  ($scope, $element) ->
    $scope.annotations = []    

    #sock.onopen = ->
    #sock.onclose = ->
    sock.onmessage = (msg) =>
      $scope.$apply =>
        console.log msg.data
        $scope.annotations.push msg.data
  )
  .filter('fuzzyTime', -> fuzzyTime)
  .filter('userName', -> userName)


