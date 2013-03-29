angular.module('h.displayer',[])
  .controller('DisplayerCtrl',
  ($scope) ->
    $scope.toggleCollapse = (event) ->
      elem = (((angular.element event.srcElement).parent()).parent()).parent()
      if elem.hasClass 'hyp-collapsed' then elem.removeClass 'hyp-collapsed'
      else elem.addClass 'hyp-collapsed'
)