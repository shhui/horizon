//var refresh_time = 60000;
horizon.d3_line_chart_ceilometer = {

	/**
   * A class representing the line chart
   * @param chart_module A context of horizon.d3_line_chart module.
   * @param html_element A html_element containing the chart.
   * @param settings An object containing settings of the chart.
   */
	LineChart: function(chart_module, html_element, settings, state) {
		var self = this;
		var jquery_element = $(html_element);
		self.chart_module = chart_module;
		self.html_element = html_element;
		self.jquery_element = jquery_element;
		self.lable = jquery_element.attr('data-y_axis');
		// Define constants tables
		var timeUnit = ['ns', 'us', 'ms', 's'];
		var bitUnit = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB', 'NB', 'DB'];
		var bitRateUnit = ['B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s', 'PB/s', 'EB/s', 'ZB/s', 'YB/s', 'NB/s', 'DB/s'];
		var packUnit = ['packet', 'K packet'];
		var packRateUnit = ['packet/s', 'K packet/s'];
		var proUnit = ['process', 'K process'];

		if (state !== undefined) {
			self.hist_series = state.hist_series;
			self.interval_time = state.interval_time;
		}
        

		/************************************************************************/
		/*********************** Initialization methods *************************/
		/************************************************************************/
		/**
		 * Initialize object
		 */
		self.init = function() {			
			var self = this;			
			/* TODO(lsmola) make more configurable init from more sources */
			self.legend_element = $(jquery_element.data('legend-selector')).get(0);
			self.slider_element = $(jquery_element.data('slider-selector')).get(0);

			self.url = jquery_element.data('url');
			self.url_parameters = jquery_element.data('url_parameters');

			self.final_url = self.url;
			if (jquery_element.data('form-selector')) {
				$(jquery_element.data('form-selector')).each(function() {
					// Add serialized data from all connected forms to url.
					if (self.final_url.indexOf('?') > -1) {
						self.final_url += '&' + $(this).serialize();
					} else {
						self.final_url += '?' + $(this).serialize();
					}
				});
			}
			if (self.interval_time != undefined) {
				if (self.final_url.indexOf('?') > -1) {
					self.final_url += '&interval_time=' + self.interval_time;
				} else {
					self.final_url += '?interval_time' + self.interval_time;
				}
			}
			self.data = [];
			self.color = d3.scale.category10();

			// Self aggregation and statistic attrs
			self.stats = {};
			self.stats.average = 0;
			self.stats.last_value = 0;

			// Load initial settings.
			self.init_settings(settings);
			// Get correct size of chart and the wrapper.
			self.get_size();
		};
		/**
		 * Initialize settings of the chart with default values, then applies
		 * defined settings of the chart. Settings are obtained either from JSON
		 * of the html attribute data-settings, or from init of the charts. The
		 * highest priority settings are obtained directly from the JSON data
		 * obtained from the server.
		 * @param settings An object containing settings of the chart.
		 */
		self.init_settings = function(settings) {
			var self = this;

			self.settings = {};
			self.settings.renderer = 'line';
			self.settings.auto_size = true;
			self.settings.axes_x = true;
			self.settings.axes_y = true;
			self.settings.interpolation = 'linear';
			// Static y axes values
			self.settings.yMin = undefined;
			self.settings.yMax = undefined;
			// Show last point as dot
			self.settings.higlight_last_point = false;

			// Composed charts wrapper
			self.settings.composed_chart_selector = '.overview_chart';
			// Bar chart component
			self.settings.bar_chart_selector = 'div[data-chart-type="overview_bar_chart"]';
			self.settings.bar_chart_settings = undefined;

			// allowed: verbose
			self.hover_formatter = 'verbose';

			/*
        Applying settings. The later application rewrites the previous
        therefore it has bigger priority.
      */

			// Settings defined in the init method of the chart
			if (settings) {
				self.apply_settings(settings);
			}

			// Settings defined in the html data-settings attribute
			if (self.jquery_element.data('settings')) {
				var inline_settings = self.jquery_element.data('settings');
				self.apply_settings(inline_settings);
			}
		};

		/**
		 * Applies passed settings to the chart object. Allowed settings are
		 * listed in this method.
		 * @param settings An object containing settings of the chart.
		 */
		self.apply_settings = function(settings) {
			var self = this;

			var allowed_settings = ['renderer', 'auto_size', 'axes_x', 'axes_y', 'interpolation', 'yMin', 'yMax', 'bar_chart_settings', 'bar_chart_selector', 'composed_chart_selector', 'higlight_last_point'];

			jQuery.each(allowed_settings,
			function(index, setting_name) {
				if (settings[setting_name] !== undefined) {
					self.settings[setting_name] = settings[setting_name];
				}
			});
		};

		/**
		 * Computes size of the chart from surrounding divs. When
		 * settings.auto_size is on, it stretches the chart to bottom of
		 * the screen.
		 */
		self.get_size = function() {
			/*
			   The height will be determined by css or window size,
			   I have to hide everything inside that could mess with
			   the size, so it is fully determined by outer CSS.
			   */
			$(self.html_element).css('height', '');
			$(self.html_element).css('width', '');
			var svg = $(self.html_element).find('svg');
			svg.hide();

			/*
			   Width an height of the chart will be taken from chart wrapper,
			   that can be styled by css.
			   */
			self.width = jquery_element.width();

			// Set either the minimal height defined by CSS.
			self.height = jquery_element.height();

			/*
			   Or stretch it to the remaining height of the window if there
			   is a place. + some space on the bottom, lets say 30px.
			   */
			if (self.settings.auto_size) {
				var auto_height = $(window).height() - jquery_element.offset().top - 30;
				if (auto_height > self.height) {
					self.height = auto_height;
				}
			}

			/* Setting new sizes. It is important when resizing a window.*/
			$(self.html_element).css('height', self.height);
			$(self.html_element).css('width', self.width);
			svg.show();
			svg.css('height', self.height);
			svg.css('width', self.width);
		};

		/************************************************************************/
		/****************************** Initialization **************************/
		/************************************************************************/
		// Init of the object
		self.init();

		/************************************************************************/
		/****************************** Methods *********************************/
		/************************************************************************/
		/**
		 * Obtains the actual chart data and renders the chart again.
		 */
		self.refresh = function() {
			var self = this;
			var interval_time = self.interval_time;
			if (jquery_element.attr('data-display') == 'false') {
				return false;
			}
			if (self.interval_time == undefined) {
				self.start_loading();
			}
			horizon.ajax.queue({
				url: self.final_url,
				success: function(data, textStatus, jqXHR) {
					// Clearing the old chart data.
					$(self.html_element).html('');
					$(self.legend_element).html('');
					self.interval_time = data.last_time.date_time;
					if (data.series.length == 0) {
						if(self.hist_series != undefined) {
							data.series = $.extend(true, [], self.hist_series);
						}
					} else {						
						// if (meterArray[jquery_element.attr('data-meter')] != null) {
                        if (self.hist_series !== undefined) {
                            if (jquery_element.attr('data-increm') == undefined){
								for (j = 0; j < data.series.length; j++) {
									self.hist_series[j].data = 
										self.hist_series[j].data.concat(data.series[j].data);                                
									var latest_x = data.series[j].data[data.series[j].data.length-1].x;
									var oldest_local = new Date(Date.parse(latest_x) - 8*60*60*1000);
									var index = -1;
									for (var i = 0; i < self.hist_series[j].data.length; i ++) {
										var date_local = new Date(Date.parse(self.hist_series[j].data[i].x));
										if (date_local >= oldest_local) {
											index = i;
											break;
										}
									}
									if (index != -1) {
										self.hist_series[j].data.splice(0, index + 1);
									}
								}
						    }							
							data.series = $.extend(true, [], self.hist_series);
						} else {
							self.hist_series = $.extend(true, [], data.series);							
						}
					}
					
					self.series = data.series;
					self.stats = data.stats;
                    
					// The highest priority settings are sent with the data.
					self.apply_settings(data.settings);

					if (self.series.length <= 0) {
						$(self.html_element).html(gettext('No data available.'));
						$(self.legend_element).html('');
						// Setting a fix height breaks things when legend is getting
						// bigger.
						$(self.legend_element).css('height', '');
					} else {
						self.render();
					}
				},
				error: function(jqXHR, textStatus, errorThrown) {
					$(self.html_element).html(gettext('No data available.'));
					$(self.legend_element).html('');
					// Setting a fix height breaks things when legend is getting
					// bigger.
					$(self.legend_element).css('height', '');
					// FIXME add proper fail message
					if (jqXHR.status != 0) {
						horizon.alert('error', gettext('An error occurred. Please try again later.'));
					}
				},
				complete: function(jqXHR, textStatus) {
					self.finish_loading();
				}
			});
		};

		/**
	 	* Renders the chart using Rickshaw library.
		*/
		self.render = function() {
			var self = this;
			var last_point = undefined;
			var last_point_color = undefined;

			var converNum = 0;
			var arrUnit = new Array();
			var ymax = 0; //The maximum value of y axis
			var need_convert_unit = false; // unit conver flag
			if (jquery_element.attr('data-unit-conver') == 'true') {
				var xNum = 0; //total of points
				var meterNum = 0; // num of meter
				var arrTotal = new Array();
				$.map(self.series, function(serie) {
					var total = 0; //total of value of y axis
					$.map(serie.data, function(statistic) {
						total = total + statistic.y;
						xNum++;
					});
					arrTotal[meterNum] = total;
					arrUnit[meterNum] = serie.unit;
					meterNum++;
				});
				for (var i = 0; i < meterNum; i++) {
					var avg = arrTotal[i] / xNum;
					if (avg > 0) {
						var unit = getValue(arrUnit[i]);
						var n = 0; // unit conver num
						n = mi(avg, unit, n);
						var max_mi = after(arrUnit[i]);
						if (n > max_mi) {
							n = max_mi;
						}
						if (n > 0) {
							need_convert_unit = true;
							// Use the min convert times
							if (n > converNum || converNum == 0) {
								converNum = n;
							}
						}
					}
				}
			}
			$.map(self.series, function(serie, index) {
				serie.color = last_point_color = self.color(serie.name);
				if (need_convert_unit) {
					serie.unit = converUnit(serie.unit, converNum);
				}
				// Add unit to y axis lable
				if (index == 0 && ')' != self.lable.charAt(self.lable.length)) {
					self.lable = self.lable + serie.unit + ')';
				}
				$.map(serie.data, function(statistic) {
					// need to parse each date
					statistic.x = d3.time.format('%Y-%m-%dT%H:%M:%S').parse(statistic.x);
					statistic.x = statistic.x.getTime() / 1000;
					last_point = statistic;
					last_point.color = serie.color;
					if (need_convert_unit) {
						for (var i = 0; i < converNum; i++) {
							var unit = getValue(arrUnit[i]);
							statistic.y = statistic.y / unit;
						}
					}
					if (statistic.y > ymax) {
						ymax = statistic.y;
					}
				});
				// Leave 10% top margin
				ymax = ymax * 10 / 9;
				self.apply_settings({'yMax': ymax});
			});

			var renderer = self.settings.renderer;
			if (renderer === 'StaticAxes') {
				renderer = Rickshaw.Graph.Renderer.StaticAxes;
			}

			// instantiate our graph!
			var graph = new Rickshaw.Graph({
				element: self.html_element,
				width: self.width,
				height: self.height,
				renderer: renderer,
				series: self.series,
				min: self.settings.yMin,
				max: self.settings.yMax,
				interpolation: self.settings.interpolation
			});
			graph.render();

			if (self.hover_formatter === 'verbose') {
				var hoverDetail = new Rickshaw.Graph.HoverDetail({
					graph: graph,
					formatter: function(series, x, y) {
						//var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
						var d = new Date(x * 1000);
						d.setTime(d.getTime() - (d.getTimezoneOffset() * 60000));
						//var date = '<span class="date">' + d.toString() + '</span>';
						var date = '<span class="date">' + d.toLocaleString() + '</span>';
						var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
						var content = swatch + series.name + ': ' + parseFloat(y).toFixed(2) + ' ' + series.unit + '<br>' + date;
						return content;
					}
				});
			}

			if (self.legend_element) {
				var legend = new Rickshaw.Graph.Legend({
					graph: graph,
					element: self.legend_element
				});

				var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
					graph: graph,
					legend: legend
				});

				var order = new Rickshaw.Graph.Behavior.Series.Order({
					graph: graph,
					legend: legend
				});

				var highlighter = new Rickshaw.Graph.Behavior.Series.Highlight({
					graph: graph,
					legend: legend
				});
			}
			if (self.settings.axes_x) { 
				
				var axes_x = new Rickshaw.Graph.Axis.Time({
					graph: graph
				});
				axes_x.render();
			}
			if (self.settings.axes_y) {
				var axes_y = new Rickshaw.Graph.Axis.Y({
					graph: graph,
					tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
					lable: self.lable
				});
				axes_y.render();
			}
		};

		/**
		 * Shows chart loader with backdrop. Backdrop is computed to hide
		 * the canvas with chart. Loader is computed to be placed in the center.
		 * Hides also a block with legend.
		 */
		self.start_loading = function() {
			var self = this;

			/* Find and remove backdrops and spinners that could be already there.*/
			$(self.html_element).find('.modal-backdrop').remove();
			$(self.html_element).find('.spinner_wrapper').remove();

			// Display the backdrop that will be over the chart.
			self.backdrop = $('<div class="modal-backdrop"></div>');
			self.backdrop.css('width', self.width).css('height', self.height);
			$(self.html_element).append(self.backdrop);

			// Hide the legend.
			$(self.legend_element).html('').addClass('disabled');

			// Show the spinner.
			self.spinner = $('<div class="spinner_wrapper"></div>');
			$(self.html_element).append(self.spinner);
			/*
			TODO(lsmola) a loader for in-line tables spark-lines has to be
			prepared, the parameters of loader could be sent in settings.
			 */
			self.spinner.spin(horizon.conf.spinner_options.line_chart);

			// Center the spinner considering the size of the spinner.
			var radius = horizon.conf.spinner_options.line_chart.radius;
			var length = horizon.conf.spinner_options.line_chart.length;
			var spinner_size = radius + length;
			var top = (self.height / 2) - spinner_size / 2;
			var left = (self.width / 2) - spinner_size / 2;
			self.spinner.css('top', top).css('left', left);
		};

		/**
		 * Hides the loader and backdrop so the chart will become visible.
		 * Shows also the block with legend.
		 */
		self.finish_loading = function() {
			var self = this;
			// Showing the legend.
			$(self.legend_element).removeClass('disabled');
		};

		/**
		 * Util methods
		 */
		/**
		 * the unit when 'unit' convert 'n' times 
		 */
		var converUnit = function(unit, n) {
			n = parseInt(n);
			var unitRes = unit;
			var tIndex = timeUnit.indexOf(unit);
			tIndex = parseInt(tIndex);
			if (tIndex != -1) {
				if (tIndex + n < timeUnit.length) {
					unitRes = timeUnit[tIndex + n];
					return unitRes;
				}
			}
			var bIndex = bitUnit.indexOf(unit);
			bIndex = parseInt(bIndex);
			if (bIndex != -1) {
				if (bIndex + n < bitUnit.length) {
					unitRes = bitUnit[bIndex + n];
					return unitRes;
				}
			}
			var bRateIndex = bitRateUnit.indexOf(unit);
			bRateIndex = parseInt(bRateIndex);
			if (bRateIndex != -1) {
				if (bRateIndex + n < bitRateUnit.length) {
					unitRes = bitRateUnit[bRateIndex + n];
					return unitRes;
				}
			}

			var paIndex = packUnit.indexOf(unit);
			paIndex = parseInt(paIndex);
			if (paIndex != -1) {
				if (paIndex + n < packUnit.length) {
					unitRes = packUnit[paIndex + n];
					return unitRes;
				}
			}
			var paRateIndex = packRateUnit.indexOf(unit);
			paRateIndex = parseInt(paRateIndex);
			if (paRateIndex != -1) {
				if (paRateIndex + n < packRateUnit.length) {
					unitRes = packRateUnit[paRateIndex + n];
					return unitRes;
				}
			}

			var prIndex = proUnit.indexOf(unit);
			prIndex = parseInt(prIndex);
			if (prIndex != -1) {
				if (prIndex + n < prIndex.length) {
					unitRes = proUnit[prIndex + n];
					return unitRes;
				}
			}
			return unitRes;
		};
		/**
		 * how many object after 'unit' in array
		 */
		var after = function(unit) {
			var n = 0;
			var tIndex = timeUnit.indexOf(unit);
			if (tIndex != -1) {
				n = timeUnit.length - 1 - tIndex;
				return n;
			}
			var bIndex = bitUnit.indexOf(unit);
			if (bIndex != -1) {
				n = bitUnit.length - 1 - bIndex;
				return n;
			}
			var bRateIndex = bitRateUnit.indexOf(unit);
			if (bRateIndex != -1) {
				n = bitRateUnit.length - 1 - bRateIndex;
				return n;
			}

			var paIndex = packUnit.indexOf(unit);
			if (paIndex != -1) {
				n = packUnit.length - 1 - paIndex;
				return n;
			}
			var paRateIndex = packRateUnit.indexOf(unit);
			if (paRateIndex != -1) {
				n = packRateUnit.length - 1 - paRateIndex;
				return n;
			}
			var prIndex = proUnit.indexOf(unit);
			if (prIndex != -1) {
				n = proUnit.length - 1 - prIndex;
				return n;
			}
			return n;
		};
		/**
		 * Recursive function 
		 * for example: 
		 * num 789 unit 1024 n 0 return n 0
		 * num 123456 unit 1000 n 0 return 1
		 * num 12345678 unit 1000 n 0 return 2
		 */
		var mi = function(num, unit, n) {
			if (unit == 1) {
				return n;
			}
			if (num > unit) {
				n = n + 1;
				if (num / unit > unit) {
					return mi(num / unit, unit, n);
				} else {
					return n;
				}
			} else {
				return n;
			}
		};
		/**
		 * get value of unit 
		 */
		var getValue = function(unit) {
			var val;
			if (unit == 's' || unit == 'ns' || unit == 'packet' || unit == 'packet/s' || unit == 'process') {
				val = 1000;
			} else if (unit == 'B'|| unit == 'KB' || unit == 'MB' || unit == 'B/s') {
				val = 1024;
			} else {
				val = 1;
			}
			return val;
		};

	},

	/**
   * Function for initializing of the charts.
   * If settings['auto_resize'] is true, the chart will be refreshed when
   * the size of the window is changed. This option made only sense when
   * the size of the chart and its wrapper is not static.
   * @param selector JQuery selector of charts we want to initialize.
   * @param settings An object containing settings of the chart.
   */
	init: function(selector, settings, flag) {
		var self = this;
		self.refresh_time = $('#refresh_cycle').val();
		$(selector).each(function() {
			self.refresh(this, settings, flag);
		});
		if (settings !== undefined && settings.auto_resize) {
			/*
			I want to refresh chart on resize of the window, but only
			at the end of the resize. Nice code from mr. Google.
			 */
			var rtime = new Date(1, 1, 2000, 12, 0, 0);
			var timeout = false;
			var delta = 400;
			$(window).resize(function() {
				rtime = new Date();
				if (timeout === false) {
					timeout = true;
					setTimeout(resizeend, delta);
				}
			});

			var resizeend = function() {
				if (new Date() - rtime < delta) {
					setTimeout(resizeend, delta);
				} else {
					timeout = false;
					$(selector).each(function() {
						self.refresh(this, settings);
					});
				}
			};
		}
	    self.bind_commands(selector, settings);
	},
	/**
   * Function for creating chart objects, saving them for later reuse
   * and calling their refresh method.
   * @param html_element HTML element where the chart will be rendered.
   * @param settings An object containing settings of the chart.
   * @param auto_refresh if auto refresh the chart 
   * @param old_chart to get the history chart states 
   */
	refresh: function(html_element, settings, auto_refresh, old_chart) {
		var self = this;
		var state = undefined
        if (old_chart !== undefined) {
		    state = {"hist_series" : old_chart.hist_series, 
	                 "interval_time" : old_chart.interval_time}
        }  

		var chart = new this.LineChart(this, html_element, settings, state);
		/*
      FIXME save chart objects somewhere so I can use them again when
      e.g. I am switching tabs, or if I want to update them
      via web sockets
      this.charts.add_or_update(chart)
    */
		chart.refresh();

		var interval_id = "";
		if (auto_refresh) {
			interval_id= setInterval(function() {
				inner_fun()
			},
			self.refresh_time);
		}
				
		function inner_fun() {
			clearInterval(interval_id);
			horizon.d3_line_chart_ceilometer.refresh(html_element, 
				settings, auto_refresh, chart);
		}
	},
	bind_commands: function (selector, settings){
	    // connecting controls of the charts
	    var select_box_selector = 'select[data-line-chart-command="select_box_change"]';
	    var datepicker_selector = 'input[data-line-chart-command="date_picker_change"]';
	    var self = this;

	    /**
	     * Connecting forms to charts it controls. Each chart contains
	     * JQuery selector data-form-selector, which defines by which
	     * html Forms is a particular chart controlled. This information
	     * has to be projected to forms. So when form input is changed,
	     * all connected charts are refreshed.
	     */
	    connect_forms_to_charts = function(){
	      $(selector).each(function() {
	        var chart = $(this);
	        $(chart.data('form-selector')).each(function(){
	          var form = $(this);
	          // each form is building a jquery selector for all charts it affects
	          var chart_identifier = 'div[data-form-selector="' + chart.data('form-selector') + '"]';
	          if (!form.data('charts_selector')){
	            form.data('charts_selector', chart_identifier);
	          } else {
	            form.data('charts_selector', form.data('charts_selector') + ', ' + chart_identifier);
	          }
	        });
	      });
	    };

	    /**
	     * A helper function for delegating form events to charts, causing their
	     * refreshing.
	     * @param selector JQuery selector of charts we are initializing.
	     * @param event_name Event name we want to delegate.
	     * @param settings An object containing settings of the chart.
	     */
	    delegate_event_and_refresh_charts = function(selector, event_name, settings) {
	      $('form').delegate(selector, event_name, function() {
	        /*
	          Registering 'any event' on form element by delegating. This way it
	          can be easily overridden / enhanced when some special functionality
	          needs to be added. Like input element showing/hiding another element
	          on some condition will be defined directly on element and can block
	          this default behavior.
	        */
	        var invoker = $(this);
	        var form = invoker.parents('form').first();

	        $(form.data('charts_selector')).each(function(){
	          // refresh the chart connected to changed form
	          self.refresh(this, settings);
	        });
	      });
	    };

	    /**
	     * A helper function for catching change event of form selectboxes
	     * connected to charts.
	     */
	    bind_select_box_change = function(settings) {
	      delegate_event_and_refresh_charts(select_box_selector, 'change', settings);
	    };

	    /**
	     * A helper function for catching changeDate event of form datepickers
	     * connected to charts.
	     */
	    bind_datepicker_change = function(settings) {
	      var now = new Date();

	      $(datepicker_selector).each(function() {
	        var el = $(this);
	        el.datepicker({format: 'yyyy-mm-dd',
	          setDate: new Date(),
	          showButtonPanel: true});
	      });
	      delegate_event_and_refresh_charts(datepicker_selector, 'changeDate', settings);
	    };

	    connect_forms_to_charts();
	    bind_select_box_change(settings);
	    bind_datepicker_change(settings);
	  },
	switchTime: function() {
		var self = this;
		var value = $('#refresh_cycle').val();
		self.refresh_time = parseInt(value);
		
		//interval_time = '&interval_time=' + refresh_time / 1000;
		//horizon.d3_line_chart_ceilometer.init('div[data-chart-type="line_chart"]', {
		//	'auto_resize': true
		//});
	},
	showCPU: function() {
		var cupdiv = $('#cpu_cup_util');
		var elem = $(cupdiv).find('.chart');
		var bgimage = $('#cpu_title_image');
		this.switchImage(cupdiv, bgimage, elem);
	},
	showNetworkBytes: function() {
		var networkBytediv = $('#network_bytes');
		var elem = $(networkBytediv).find('.chart');
		var bgimage = $('#network_bytes_image');
		this.switchImage(networkBytediv, bgimage, elem);
	},
	switchImage: function(obj, bgimage, elem) {
		if (obj.css('display') == "none") {
			obj.css('display', 'block');
			elem.attr('data-display', true);
			bgimage.css("background-image", "url(/static/dashboard/img/drop_arrow_l2.png)");
		} else {
			obj.css('display', 'none');
			elem.attr('data-display', false);
			bgimage.css("background-image", "url(/static/dashboard/img/right_droparrow_l2.png)");
		}
	},
	switchUnit: function (obj) {
		var legend = $("#meter option:selected").attr("legend");
		$("div[data-chart-type='line_chart']").attr('data-y_axis', legend);
	},

	/**
	 * export csv
	 * @param base_url Export csv document page url.
	 */
	export_csv: function (base_url) {
		var resource_id = $("#resource_id").val();
		var meter = $("#meter").find("option:selected").val();
		var period = $("#period").find("option:selected").val();
		var stats_attr = $("#stats_attr").find("option:selected").val();
		var date_options = $("#date_options").find("option:selected").val();
		var group_by = $("#group_by").val();
		var query = "?format=csv";
		if (!(resource_id == undefined)) {
		    query += "&resource_id=" + resource_id;
		    // If filter by resource_id, no need to group results
		    if (!(group_by == undefined)) {
	 	        query += "&group_by=" + group_by;
	 	    }
		}
		query += "&meter=" + meter;
		if (!(period == undefined) ){
		    query += "&period=" + period;
		} else {
		    query += "&period=";
		}
			
		query += "&stats_attr=" + stats_attr;
		if ($("#date_options").find("option:selected").val() == "other") {
		    var date_from = $("#date_from").val();
		    var date_to = $("#date_to").val();
		    query += "&date_options=" + date_options;
		    query += "&date_from=" + date_from;
		    query += "&date_to=" + date_to;
		} else {
		    query += "&date_options=" + date_options;
		}
		//href = window.location + '';
		//n = href.indexOf('admin');
		//var len = href.length;
		//var str = href.substring(n, len)
	
		query = base_url + query;
	
		window.location.href = query;
	}
};
/* Init the graphs */
/* horizon.addInitFunction(function () { 
horizon.d3_line_chart_ceilometer.init('div[data-chart-type="line_chart"]', 
{'auto_resize': true}); }); */
