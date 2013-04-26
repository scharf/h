var _rollbarParams = {"server.environment": "development.unit07"};
_rollbarParams["notifier.snippet_version"] = "2";
var _rollbar=["c62e426006d745b88f4d3cea7cfffc92", _rollbarParams];
var _ratchet=_rollbar;

(function(){
  window.onerror=function(e,u,l) {
    console.log("Reporting host page error to Rollbar...");
    _rollbar.push({_t:'uncaught',e:e,u:u,l:l});
  };
  var s=document.createElement("script");
  s.src="//d37gvrvc0wt4s1.cloudfront.net/js/1/rollbar.min.js";
  document.body.appendChild(s);
})();
