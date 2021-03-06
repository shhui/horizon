horizon.addInitFunction(function() {
  var allPanelGroupBodies = $('.nav_accordion > dd > div > ul');

  allPanelGroupBodies.each(function(index, value) {
    var activePanels = $(this).find('li > a.active');
    if(activePanels.length === 0) {
      $(this).slideUp(0);
    }
    //add 
    else {
      var iChildren = $(this).prev().children().children();
      iChildren.each(function(index, value) {
        if ($(this).hasClass('fa fa-caret-right')) {
          $(this).removeClass('fa fa-caret-right').addClass('fa fa-caret-down');
        }  
      })
    }
  });

  // mark the active panel group
  var activePanel = $('.nav_accordion > dd > div > ul > li > a.active');
  activePanel.closest('div').find('h4').addClass('active');

  // dashboard click
  $('.nav_accordion > dt').click(function() {
    var myDashHeader = $(this);
    var myDashWasActive = myDashHeader.hasClass("active");

    // mark the active dashboard
    var allDashboardHeaders = $('.nav_accordion > dt');
    allDashboardHeaders.removeClass("active");

    // collapse all dashboard contents
    var allDashboardBodies = $('.nav_accordion > dd');
    allDashboardBodies.slideUp();

    // if the current dashboard was active, leave it collapsed
    if(!myDashWasActive) {
      myDashHeader.addClass("active");

      // expand the active dashboard body
      var myDashBody = myDashHeader.next();
      myDashBody.slideDown();

      var activeDashPanel = myDashBody.find("div > ul > li > a.active");
      // if the active panel is not in the expanded dashboard
      if (activeDashPanel.length === 0) {
        // expand the active panel group
        var activePanel = myDashBody.find("div:first > ul");
        activePanel.slideDown();
        activePanel.closest('div').find("h4").addClass("active");

        //add
        var iTagChildren = myDashHeader.next().find("div > h4.active").children().children();
        iTagChildren.each(function(){
          if ($(this).hasClass('fa fa-caret-right')) {
            $(this).removeClass('fa fa-caret-right').addClass('fa fa-caret-down');
          } 
        })

        // collapse the inactive panel groups
        var nonActivePanels = myDashBody.find("div:not(:first) > ul");
        nonActivePanels.slideUp();
      }
      // the expanded dashboard contains the active panel
      else
      {
        // collapse the inactive panel groups
        activeDashPanel.closest('div').find("h4").addClass("active");
        allPanelGroupBodies.each(function(index, value) {
          var activePanels = value.find('li > a.active');
          if(activePanels.length === 0) {
            $(this).slideUp();
          }
        });
      }
    }
    return false;
  });

  // panel group click
  $('.nav_accordion > dd > div > h4').click(function() {
    //add
    var actDivChild = $('.nav_accordion > dd > div > h4.active').children().children();
    actDivChild.each(function(){
      if ($(this).hasClass('fa fa-caret-down')) {
        $(this).removeClass('fa fa-caret-down').addClass('fa fa-caret-right');
      } 
    })

    var myPanelGroupHeader = $(this);
    myPanelGroupWasActive = myPanelGroupHeader.hasClass("active");

    // collapse all panel groups
    var allPanelGroupHeaders = $('.nav_accordion > dd > div > h4');
    allPanelGroupHeaders.removeClass("active");

    //add 
    var iTag = $(this).children().children();
    iTag.each(function(){
      if ($(this).hasClass('fa fa-caret-down')) {
        $(this).removeClass('fa fa-caret-down').addClass('fa fa-caret-right');
      } 
    })

    allPanelGroupBodies.slideUp();


    // expand the selected panel group if not already active
    if(!myPanelGroupWasActive) {
      myPanelGroupHeader.addClass("active");
      //add
      iTag.each(function(){
        if ($(this).hasClass('fa fa-caret-right')) {
          $(this).removeClass('fa fa-caret-right').addClass('fa fa-caret-down');
        } 
      })

      myPanelGroupHeader.closest('div').find('ul').slideDown();
    }
  });

  // panel selection
  $('.nav_accordion > dd > ul > li > a').click(function() {
    horizon.modals.modal_spinner(gettext("Loading"));
  });

});
