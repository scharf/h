class Annotator.Plugin.ProgressBox extends Annotator.Plugin

  # prototype constants

  # heatmap svg skeleton
  html: """
        <div class="annotator-progress-box">
        50% - Doing Something
        </div>
        """

  constructor: (element, options) ->
    super $(@html), options
    @element.appendTo element

  # Progress should be a number between 0 and 1
  updateProgress: (task, progress) ->
        
    # Are we ready?
    if progress is 1
      this.finished task
      return

    # Did we got a valid value?
    unless 0 <= progress < 1
      throw new Error "Invalid param to updateProgress! Should be in the [0;1] range. (Got " + progress + ")"

    # OK, business as usual
    progressText = (100 * progress).toString() + "%"
    console.log "Task '" + task + "': " + progressText
    @element.removeClass "annotator-hide"
    @element.text progressText + " " + task

  # We are ready.
  finished: (task) ->
    console.log "Task '" + task + "' finished!"
    @element.text "."
    @element.addClass "annotator-hide"
    