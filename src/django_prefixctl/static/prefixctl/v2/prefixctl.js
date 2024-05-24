(function($, $tc, $ctl) {


$ctl.application.Prefixctl = $tc.extend(
  "Prefixctl",
  {
    Prefixctl : function() {
      this.Application("prefixctl");
      this.$c.header.app_slug = "prefix";

      this.tool("prefix_sets", () => {
        return new $ctl.application.Prefixctl.PrefixSets();
      });
      this.$t.prefix_sets.activate();

      this.tool("asn_sets", () => {
        return new $ctl.application.Prefixctl.ASNSets();
      });
      this.$t.asn_sets.activate();
      $($ctl.application).trigger("prefixctl-ready", [this]);

      this.autoload_page();
    }
  },
  $ctl.application.Application
);

/**
 * Monitor registry
 * @class Monitors
 */

$ctl.application.Prefixctl.Monitors = $tc.define(
  "Monitors",
  {
    Monitors: function() {
      this.monitors = {};
    },
    /**
     * open the monitor modal for the specified monitor name
     *
     * @method modal
     * @param {String} name - monitor name (handle ref tag)
     * @param {Object} prefix_set - api response object
     * @param {Object} monitor - api response object
     * @returns
     */
    modal: function(name, prefix_set, monitor) {
      return this.monitors[name].modal(prefix_set, monitor);
    },

    /**
     * register a monitor class
     *
     * monitor_class object needs to have following properties:
     *
     * - name: monitor name (handle ref tag)
     * - permissions: array of permissions that the user needs to have to view the monitor
     * - label: display name of the monitor
     * - modal: function that opens the monitor modal for creation or editing
     *
     * @method register
     * @param {Object} monitor_class - monitor class
     */
    register: function(monitor_class) {
      this.monitors[monitor_class.name] = monitor_class;
    },

    /**
     * @method list
     * @returns {Array} list of monitor classes
     */
    list: function() {
      return Object.values(this.monitors);
    },

    /**
     * @method permissioned_list
     * @returns {Array} list of monitor classes that the user has permission to view
     */
    permissioned_list: function() {
      const monitor_classes = [];
      for (const [key, value] of Object.entries(this.monitors)) {
        for (const permission of value.permissions) {
          // all permissions need to be true
          if(!grainy.check(`${permission}.${$ctl.org.id}`, "r")) {
            return [];
          }
        }
        monitor_classes.push(value.name);
      }
      return monitor_classes;
    }
  }
)

// prefix set monitors
$ctl.application.Prefixctl.PrefixSetMonitors = new $ctl.application.Prefixctl.Monitors();

// asn set monitors
$ctl.application.Prefixctl.ASNSetMonitors = new $ctl.application.Prefixctl.Monitors();

$ctl.application.Prefixctl.PrefixMonitorList = $tc.extend(
  "PrefixMonitorList",
  {
    build_row : function(data) {

      const monitor_type = data.monitor_type;

      if(monitor_type != "prefix_monitor") {
        console.log("monitor type not supported: "+monitor_type)
        const node = $ctl.template("monlist_"+monitor_type);
        if(!node.length)
          return $('<div>');
        return node;
      }

      return this.List_build_row(data);
    }
  },
  twentyc.rest.List
);

$ctl.application.Prefixctl.CheckboxKeepListOpen = $tc.extend(
  "CheckboxKeepListOpen",
  {
    CheckboxKeepListOpen : function(prefix_set, jq) {
      this.prefix_set = prefix_set;
      this.bind_to_event = "click";
      this.Button(jq);
    },

    format_request_url : function(url) {
      return url.replace("prefixset_id", this.prefix_set.id);
    },

    payload : function() {
      var data = {...this.prefix_set}
      data.ux_keep_list_open = this.element.prop("checked");
      return data;
    }
  },
  twentyc.rest.Button
)

$ctl.application.Prefixctl.PrefixSets = $tc.extend(
  "PrefixSets",
  {
    PrefixSets : function() {
      this.Tool("prefix_sets");
    },

    init : function() {
      const prefix_search_url = this.jquery.find(".prefix-searchbar").data("api-prefix-search");
      const prefixset_search_url = this.jquery.find(".prefix-searchbar").data("api-prefixset-search");
      this.widget("list", ($e) => {
        return new $ctl.application.Prefixctl.PrefixSetList(
          this.template("list", this.$e.body),
          prefix_search_url,
          prefixset_search_url
        );
      })

      this.$w.list.formatters.row = (row, data) => {
        row.find('a[data-action="edit_prefix_set"]').click(() => {
          this.prompt_edit_prefix_set(row.data("apiobject"))
        });
        row.find('a[data-action="list_prefixes"]').click(() => {
          this.toggle_prefixes(row.data("apiobject"), row)
        });

        const name_field = row.find('td[data-field="name"]')
        const prefixsetDate = new Date(data.created);
        const currentDate = new Date();
        const timeDifference = currentDate - prefixsetDate;

        const millisecondsInADay = 1000 * 60 * 60 * 24;
        const daysDifference = Math.floor(timeDifference / millisecondsInADay);
        const dayText = daysDifference === 1 ? 'day' : 'days';
        name_field.html(name_field.html() + `<span style="font-weight: normal;font-size: 15px">(${daysDifference} ${dayText} old)</span>`)

        const add_monitor_button = row.find('a[data-action="add_monitor"]');
        if (this.is_user_add_monitor_allowed()) {
          add_monitor_button.click(() => {
            this.prompt_add_prefix_monitor(row.data("apiobject"))
          });
        } else {
          add_monitor_button.parent().hide()
        }

        row.find('a[data-action="add_prefixes"]').click(() => {
          new $ctl.application.Prefixctl.ModalBulkAddPrefixes(row.data("apiobject"));
        });

        row.find('.searchbar').focus(() => {
          this.expand_prefixes(data, row);
        });
        row.find('.searchbar').keyup(function(){
          let prefixes = row.data("prefix-list").list_body.find(".prefix-container");
          let keyword = $(this).val().toLowerCase();
          if(keyword == "")
            prefixes.show();
          else {
            prefixes.each(function(element) {
              let title = $(this).find('.prefix').text().toLowerCase();
              (title.startsWith(keyword)) ? $(this).show() : $(this).hide();
            });
          }
        });


        var keep_list_open = new $ctl.application.Prefixctl.CheckboxKeepListOpen(
          data, (row.find('.ux-keep-list-open'))
        );

        $(keep_list_open).on("api-write:success", (ev, endpoint, payload)=> {
          if(payload.ux_keep_list_open)
            this.expand_prefixes(data, row);
        });

      };

      $(this.$w.list).on('insert:after', (e, row, data) => {
        var monlist = new $ctl.application.Prefixctl.PrefixMonitorList(
          $ctl.template("prefix_monitor_list")
        );

        monlist.formatters.status = $ctl.formatters.monitor_status;

        monlist.base_url = monlist.base_url.replace("/0", "/"+data.id);
        monlist.local_action('edit_prefix_monitor', (prefix_monitor, _row) => {
          this.prompt_edit_prefix_monitor(
            row.data('apiobject'), prefix_monitor
          );
        });

        $(monlist).on("load:after", () => {
          if(monlist.list_body.find('.row').length > 0) {
            monlist.element.find('div.list-empty').hide();
          } else {
            monlist.element.find('div.list-empty').show();
          }
        });

        monlist.load().then(() => {
          monlist.element.appendTo(row.filter('tr.monlist').children('td'));
        });
        row.data("monlist", monlist);

        if(data.ux_keep_list_open) {
          this.expand_prefixes(data, row);
        }


      });

      $(this.$w.list).on('remove:before', (e, data) => {
        this.collapse_prefixes(data);
      });
      this.$w.list.element.find('[data-element="button_add_prefix_set"]').click(() => {
        this.prompt_add_prefix_set();
      });
    },

    /**
     * @method is_user_add_monitor_allowed
     *
     * checks if the user has permission to add monitors
     */
    is_user_add_monitor_allowed : function() {
      return grainy.check(`prefix_monitor.${$ctl.org.id}`, "c") && grainy.check(`asn_set.${$ctl.org.id}`, "r");
    },

    prompt_add_prefix_set : function() {
      return new $ctl.application.Prefixctl.ModalPrefixSet();
    },

    prompt_remove_prefix_sets : function() {
      return new $ctl.application.Prefixctl.RemovePrefixSets();
    },

    prompt_edit_prefix_set : function(prefix_set) {
      return new $ctl.application.Prefixctl.ModalPrefixSet(prefix_set);
    },

    prompt_add_prefix_monitor : function(prefix_set) {
      let available_monitor_classes = $ctl.prefixctl.PREFIX_MONITOR_CLASSES;

      // check if user has permission to read asn sets and create prefix monitors
      if (!grainy.check(`asn_set.${$ctl.org.id}`, "r") || !grainy.check(`prefix_monitor.${$ctl.org.id}`, "c")) {
        available_monitor_classes = available_monitor_classes.filter((monitor_class) => {
          return monitor_class.tag != 'prefix_monitor';
        });
      }

      return new $ctl.application.Prefixctl.ModalSelectPrefixMonitor(prefix_set, available_monitor_classes.map((item) => item.tag));
    },

    prompt_edit_prefix_monitor : function(prefix_set, prefix_monitor) {
      return $ctl.application.Prefixctl.PrefixSetMonitors.monitors[prefix_monitor.monitor_type].modal(prefix_set, prefix_monitor);
    },

    prefixes_expanded : function(prefix_set) {
      return this.$w.list.prefixes_expanded(prefix_set);
    },

    toggle_prefixes : function(prefix_set, row) {
      if(this.prefixes_expanded(prefix_set)) {
        this.collapse_prefixes(prefix_set);
      } else {
        this.expand_prefixes(prefix_set, row);
      }
    },

    toggle_status : function(row, prefix_status) {
      if (prefix_status == 'issues'){
        row.find('.with-border').addBack('.with-border').addClass('orange-border');
        row.find('.rep-status').addClass('rep-issues');
        row.find('.rep-status').html('<b>Issues detected</b>');
      } else if (prefix_status == 'ok') {
        row.find('.with-border').addBack('.with-border').addClass('green-border');
        row.find('.rep-status').addClass('rep-ok');
        row.find('.rep-status').html('Reputation: <b>ok</b>');
      }
    },

    show_prefix_status : function(row){

      var list = row.data("prefix-list")

      if(!list) {
        return;
      }

      list.element.find('.inner-list>div').each(function() {

        var prefix_status = row.data('prefix-status');

        if(!prefix_status) {
          // prefix-status has not been loaded, bail
          return;
        }

        var prefix = $(this).attr('data-prefix');

        if(!prefix_status[prefix]) {
          // prefix doesnt exist in the report, bail
          return;
        }

        if (prefix_status[prefix].hits > 0){
          $(this).find('.prefix-rep').addClass('rep-issues').text('issues');
        } else {
          $(this).find('.prefix-rep').addClass('rep-ok').text('ok');
        }
      })
    },

    store_prefix_status : function(row, prefix_status){
		  row.data('prefix-status', prefix_status)
    },

    refresh_prefix_list : function(prefix_set) {
      var list = this.$w.list.find_row(prefix_set.id).data("prefix-list");
      if(list) {
        list.load();
      }
    },

    /**
     * expands the prefix list for the prefix set
     *
     * will do nothing if list is already expanded
     *
     * @method expand_prefixes
     * @return {Promise} promise that resolves when the list is loaded
     */

    expand_prefixes : function(prefix_set, prefix_set_row) {
      return this.$w.list.expand_prefixes(prefix_set, prefix_set_row);
    },

    collapse_prefixes : function(prefix_set) {
      return this.$w.list.collapse_prefixes(prefix_set);
    },

    menu : function() {
      let menu = this.Tool_menu();
      menu.find('[data-element="button_add_prefix_set"]').click(() => {
        this.prompt_add_prefix_set();
      });

      menu.find('[data-element="button_schedule_remove_prefix_sets"]').click(() => {
        this.prompt_remove_prefix_sets();
      });


      const searchbar = new fullctl.application.Searchbar(
        menu.find(".prefix-searchbar"),
        this.$w.list.filter.bind(this.$w.list),
        this.$w.list.clear_filter.bind(this.$w.list)
      );

      menu.find('[data-element="clear_filter"]').click(() => {
        searchbar.clear_search();
      });

      return menu;
    },

    // v2 - add bottom menu
    bottom_menu: function() {
      let bottom_menu = this.Tool_bottom_menu();
      bottom_menu.find('[data-element="button_api_view"]').attr(
        "href", this.$w.list.base_url + "/?pretty"
      )

      return bottom_menu;
    },

    activate : function() {
      this.$w.list.load();
      return this.Tool_activate();
    }
  },
  $ctl.application.Tool
);

$ctl.application.Prefixctl.PrefixSetList = $tc.extend(
  "PrefixSetList",
  {
    PrefixSetList: function(jq, prefix_search_url, prefixset_search_url) {
      this.List(jq);

      this.prefix_search_url = prefix_search_url;
      this.prefixset_search_url = prefixset_search_url;
    },

    prefixes_expanded : function(prefix_set) {
      return this.list_body.find('#prefixes-'+prefix_set.id).length > 0
    },

    /**
     * expands the prefix list for the prefix set
     *
     * will do nothing if list is already expanded
     *
     * @method expand_prefixes
     * @return {Promise} promise that resolves when the list is loaded
     */

    expand_prefixes : function(prefix_set, prefix_set_row) {
      if(this.prefixes_expanded(prefix_set)) {
        return Promise.resolve();
      }

      if(!prefix_set_row) {
        var prefix_set_row = this.find_row(prefix_set.id);
      }

      if(prefix_set_row.length > 0)
        prefix_row = prefix_set_row.find('a[data-action="list_prefixes"]').parents('tr');

      prefix_row.find('a[data-action="list_prefixes"] .icon').removeClass('icon-caret-left').addClass('icon-caret-down');

      const list = new twentyc.rest.List(
        $ctl.prefixctl.$t.prefix_sets.template('prefixes_list')
      );

      prefix_set_row.data("prefix-list", list);

      list.base_url = list.base_url.replace("/0", "/"+prefix_set.id);

      list.formatters.row = (row, data) => {
        var addon_controls = row.find(".prefix-addon-controls")
        $(this).trigger("prefix-addon-controls", [addon_controls, data, row, prefix_set_row]);
      }

      list.element.insertAfter(prefix_row);

      if(prefix_set.irr_import) {
        list.element.find('.irr-import-show').show();
        list.element.find('.irr-import-hide').hide();
      } else {
        list.element.find('.irr-import-show').hide();
        list.element.find('.irr-import-hide').show();
      }

      var form = new twentyc.rest.Form(
        list.element.find('.controls > form')
      )
      form.base_url = form.base_url.replace("/0", "/"+prefix_set.id);

      list.element.find(".btn-expand").click( () => {
          list.element.find('.mask-length-range-col').toggleClass("hidden")
      });

      $(form).on('api-write:success', () => { list.load() });
      $(list).on("load:after", () => {
        list.element.find('.inner-list>div').each(function() {
          let prefix = $(this).find('.prefix').text()
          $(this).attr('data-prefix', prefix)
          $(this).find('[data-action]').data('prefix', prefix)
	      })
      });
      list.element.attr('id', 'prefixes-'+prefix_set.id);

      return list.load();
    },

    collapse_prefixes : function(prefix_set) {
      const row = this.find_row(prefix_set.id);
      row.find('a[data-action="list_prefixes"] .icon').removeClass('icon-caret-down').addClass('icon-caret-left');

      const node = this.list_body.find('#prefixes-'+prefix_set.id)
      node.detach()
    },

    filter : function(search_term) {
      this.loading_shim.show();
      this.prefix_filter(search_term).then((result) => {
        const first_prefix_element = result.first_prefix_element;

        const except_prefixsets = result.response.map((item) => item.prefix_set);
        this.prefixset_filter(search_term, except_prefixsets).then((result) => {
          if(first_prefix_element) {
            first_prefix_element.scrollIntoView();
          }

          this.loading_shim.hide();

          // if result is empty
          if(result.length == 0 && !first_prefix_element) {
            alert("No results found")
          } else {
            $ctl.prefixctl.$t.prefix_sets.$e.menu.find('[data-element="filter_notice"]').show();
          }
        });
      });
    },

    clear_filter: function() {
      this.clear_prefix_filter();
      this.clear_prefixset_filter();
      $ctl.prefixctl.$t.prefix_sets.$e.menu.find('[data-element="filter_notice"]').hide();
    },

    /**
     * hides prefixes in the UI based on whether they match the `search_term` parameter
     * and scrolls to the first match of the `search_term`
     *
     * @method prefix_filter
     * @param {String} search_term
     * @returns {Promise} promise that resolves when the prefixes are filtered
     */

    prefix_filter: function(search_term) {
      return $.ajax({
        method : "GET",
        url : `${this.prefix_search_url}?q=${search_term}`,
      }).then((result) => {
        const matches = {}
        for (const match of result.data) {
          if (!matches[match.prefix_set]) {
            matches[match.prefix_set] = []
          }
          matches[match.prefix_set].push(match)
        }

        const list = this;
        const prefix_expand_promises = [];
        const matched_elements = [];
        this.list_body.find(".secondary.prelist").each(function() {
          const prefix_set = $(this).data('apiobject');

          if(prefix_set.id in matches) {
            const promise = list.expand_prefixes(prefix_set, $(this)).then(() => {
              $(this).attr("data-filter", 'expanded');

              const prefixes = $(this).data("prefix-list").list_body.find(".prefix-container");
              prefixes.each(function() {
                const title = $(this).find('.prefix').text().toLowerCase();
                if (title.startsWith(search_term)) {
                  matched_elements.push($(this));
                  $(this).show()
                } else {
                  $(this).hide();
                }
              });

            });

            prefix_expand_promises.push(promise);
          } else {
            if(list.prefixes_expanded(prefix_set)) {
              $(this).data("prefix-list").list_body.find(".prefix-container").hide();
            }
          }
        });

        // scroll first match into view
        return Promise.all(prefix_expand_promises).then(() => {
          // to get first element in DOM
          let jq_obj = $();
          matched_elements.forEach((element) => {
            jq_obj = jq_obj.add(element);
          });

          const first_prefix_element = jq_obj.eq(0)[0]

          return {
            "response" : result.data,
            "first_prefix_element": first_prefix_element
          };
        });
      })
    },

    /**
     * unhides all hidden prefixes in the UI, returns prefix sets to collapsed state
     * if they were expanded because of the `prefix_filter` function.
     *
     * @function clear_prefix_filter
     */
    clear_prefix_filter : function() {
      const list = this;
      this.list_body.find(".secondary.prelist").each(function() {
        if ($(this).data("prefix-list")) {
          $(this).data("prefix-list").list_body.find(".prefix-container").show();

          const prefixset_apiobj = $(this).data('apiobject')
          if($(this).attr("data-filter") == "expanded") {
            $(this).removeAttr("data-filter");
            list.collapse_prefixes(prefixset_apiobj);
          }
        }
      })
    },

    /**
     * hides prefixes in the UI based on whether they match the `search_term` parameter
     * and doesn't hide any prefixes that are in the `excempt_prefixsets_ids` array
     *
     * @method prefixset_filter
     * @param {String} search_term
     * @param {Array} excempt_prefixsets_ids
     * @returns {Promise} promise that resolves when the prefixes are filtered
     */
    prefixset_filter: function(search_term, excempt_prefixsets_ids = []) {
      return $.ajax({
        method : "GET",
        url : `${this.prefixset_search_url}?q=${search_term}`,
      }).then((result) => {
        if (result.data.length == 0) return []

        const row_ids = this.get_row_ids();
        // remove excempted prefixsets from the search results
        for (const prefix of excempt_prefixsets_ids) {
          if (row_ids.has(prefix)) {
            row_ids.delete(prefix);
          }
        }

        row_ids.forEach((id) => {
          this.hide_prefixset(id);
        });

        result.data.forEach((prefix_set) => {
          this.show_prefixset(prefix_set.id);
        });

        return result.data;
      });
    },

    clear_prefixset_filter: function() {
      const row_ids = this.get_row_ids();
      row_ids.forEach((id) => {
        this.show_prefixset(id);
      });
    },

    hide_prefixset: function(id) {
      const row = this.find_row(id);
      row.hide();
      this.list_body.find("#prefixes-"+id).hide();
    },

    show_prefixset: function(id) {
      const row = this.find_row(id);
      row.show();
      this.list_body.find("#prefixes-"+id).show();
      this.list_body.find("#prefixes-"+id).find('.prefix-container').show();
    },

    get_row_ids: function() {
      const row_ids = new Set();
      this.list_body.find("tr").each(function() {
        const prefix_set = $(this).data('apiobject');
        if (prefix_set) {
          row_ids.add(prefix_set.id);
        }
      });

      return row_ids;
    },
  },
  twentyc.rest.List
);

$ctl.application.Prefixctl.PrefixSetRemovalWidget = $tc.extend(
  "PrefixSetRemovalWidget",
  {
    PrefixSetRemovalWidget : function(jq) {
      this.Form(jq);
    },

    submit: function(method) {
      const confirmation = confirm(`Remove PrefixSets older ${this.payload().days} than old?`);
      if (!confirmation) {
        return false;
      }

      this.Form_submit(method)
    },
  },
  twentyc.rest.Form
);

/**
 * Modal for removing prefix sets that are older than the specified number of days
*/
$ctl.application.Prefixctl.RemovePrefixSets = $tc.extend(
  "RemovePrefixSets",
  {
    RemovePrefixSets : function(jq) {
      var form = this.form = new $ctl.application.Prefixctl.PrefixSetRemovalWidget(
        $ctl.template("form_old_prefixsets_removal")
      );
      var modal = this;
      var title = "Remove Prefix Sets"

      $(this.form).on(
        "api-write:success",
        function(event, endpoint, payload, response) {
          var list = $ctl.prefixctl.$t.prefix_sets.$w.list;
          list.load()
          modal.hide();
        }
      );
      this.Modal("save_right", title, form.element);
      form.wire_submit(this.$e.button_submit);

    },
  },
  $ctl.application.Modal
)

$ctl.application.Prefixctl.ModalPrefixSet = $tc.extend(
  "ModalPrefixSet",
  {
    ModalPrefixSet : function(prefix_set) {
      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_prefix_set")
      );

      var modal = this;
      var title = "Add Prefix Set"

      if(prefix_set) {
        form.fill(prefix_set)
        form.form_action = prefix_set.id
        form.method = "PUT";
        title = "Edit Prefix Set"
      }

      $(this.form).on(
        "api-write:success",
        function(event, endpoint, payload, response) {
          var data = response.first()
          var list = $ctl.prefixctl.$t.prefix_sets.$w.list;
          list.load().then(() => {
            if(!data.irr_import) {
              $ctl.prefixctl.$t.prefix_sets.expand_prefixes(data)
            }
          });
          modal.hide();
        }
      );
      this.Modal("save_right", title, form.element);
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
)

$ctl.application.Prefixctl.ModalBulkAddPrefixes = $tc.extend(
  "ModalBulkAddPrefixes",
  {
    ModalBulkAddPrefixes : function(prefix_set) {
      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_bulk_add_prefixes")
      );

      var modal = this;
      var title = "Add Prefixes"

      $(this.form).on(
        "api-write:success",
        function(event, endpoint, payload, response) {
          if(!$ctl.prefixctl.$t.prefix_sets.prefixes_expanded(prefix_set))
            $ctl.prefixctl.$t.prefix_sets.expand_prefixes(prefix_set);
          else
            $ctl.prefixctl.$t.prefix_sets.refresh_prefix_list(prefix_set);
          modal.hide();
        }
      );

      $(this.form).on("payload:after", function(event, payload) {
        // split prefixes by comma, space or newline
        payload.prefixes = payload.prefixes.split(/[\s,]+/);
      });

      this.form.format_request_url = function(url) {
        return url.replace("/0", "/"+prefix_set.id);
      };

      this.Modal("save_right", title, form.element);
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
)

$ctl.application.Prefixctl.ModalSelectPrefixMonitor = $tc.extend(
  "ModalSelectPrefixMonitor",
  {
    ModalSelectPrefixMonitor : function(prefix_set) {
      const monitor_classes = $ctl.application.Prefixctl.PrefixSetMonitors.permissioned_list();

      console.log({monitor_classes})

      // only one monitor is available to the user
      if (monitor_classes.length == 1) {
        $ctl.application.Prefixctl.PrefixSetMonitors.monitors[monitor_classes[0]].modal(prefix_set);
        return;
      }

      this.modal_ref = $ctl.application.Prefixctl.PrefixSetMonitors.monitors;

      const form = $ctl.template('form_prefix_monitor_type');
      const modal = this;
      const title = prefix_set.name + ": Add Monitor";

      this.Modal("continue", title, form);

      this.remove_unspecified_options(monitor_classes);

      this.$e.button_submit.off('click').on('click', () => {
        const sel = form.find('#monitor_type');
        modal.modal_ref[sel.val()].modal(prefix_set);
        form.attr('data-submitted', "true");
        modal.hide();
      });
    },

    /**
     * @method remove_unspecified_options
     * @param {Array[String]} monitor_classes
     *
     * removes all options from the monitor_type select that are not in the monitor_classes array
     */
    remove_unspecified_options : function(monitor_classes) {
      this.$e.body.find('[name="monitor_type"] option').each(function() {
        if (!monitor_classes.includes($(this).val())) {
          $(this).remove();
        }
      });
    }
  },
  $ctl.application.Modal
)

/**
 * Base class for PrefixCtl monitor configration modals
 */
$ctl.application.Prefixctl.ModalMonitorBase = $tc.extend(
  "ModalMonitorBase",
  {

    /**
     * initialize the monitor set up form
     *
     * @param {String} template_name
     * @param {Object} monitor
     * @returns
     */

    init_form : function(name, monitor) {
      let template_name = `form_${this.name}`
      const form = this.form = new twentyc.rest.Form(
        $ctl.template(template_name)
      );
      if(monitor) {
        form.fill(monitor)
        form.form_action = monitor.id
        form.method = "PUT";
      }

      this.modal();

      form.wire_submit(this.$e.button_submit);
      return form;
    },

    /**
     * @returns {Object} the monitor meta object from the monitor registry
     */

    meta: function() {
      if(this.prefix_set) {
        return $ctl.application.Prefixctl.PrefixSetMonitors.monitors[this.name];
      } else if (this.asn_set) {
        return $ctl.application.Prefixctl.ASNSetMonitors.monitors[this.name];
      }
    },

    /**
     * finalizes and shows the modal
     */
    modal: function() {
      this.Modal("save", this.title(), this.form.element);
    },

    /**
     * @returns {String} the modal title
     */

    title: function() {
      let monitor_label = this.meta().label;
      if(this.monitor && this.prefix_set) {
        return this.prefix_set.name + ": Edit "+monitor_label;
      }
      if(this.prefix_set) {
        return this.prefix_set.name + ": Add "+monitor_label;
      }
      if(this.monitor && this.asn_set) {
        return this.asn_set.name + ": Edit "+monitor_label;
      }
      if(this.asn_set) {
        return this.asn_set.name + ": Add "+monitor_label;
      }
    },

    /**
     * initialize the monitor as a prefix-set monitor
     */

    init_prefix_set_monitor : function() {
      const prefix_set = this.prefix_set;
      const modal = this;

      $(this.form).on(
        "api-write:before",
        function(event, endpoint, payload, method) {
          payload.prefix_set = prefix_set.id;
        }
      );

      $(this.form).on(
        "api-write:success",
        function(event, endpoint, payload, response) {
          const row = $ctl.prefixctl.$t.prefix_sets.$w.list.find_row(
            prefix_set.id
          );
          row.filter('tr.secondary').show();
          row.data("monlist").load();
          modal.hide();
        }
      );

    }
  },
  $ctl.application.Modal
)

$ctl.application.Prefixctl.ASNSets = $tc.extend(
  "ASNSets",
  {
    ASNSets : function() {
      this.Tool("asn_sets");
    },

    init : function() {
      this.delete_selected_button = this.$t.button_delete_selected;

      this.widget("list", ($e) => {
        return new $ctl.widget.SelectionList(
          this.template("list", this.$e.body),
          $(this.delete_selected_button)
        );
      });

      this.$w.list.formatters.row = (row, data) => {
        row.find('a[data-action="edit_asn_set"]').click(() => {
          this.prompt_edit_asn_set(row.data("apiobject"))
        });
        row.find('a[data-action="list_asns"]').click(() => {
          this.toggle_asns(row.data("apiobject"), row)
        });
        row.find('a[data-action="add_monitor"]').click(() => {
          this.prompt_add_asn_monitor(row.data("apiobject"))
        });


      };

      $(this.$w.list).on('insert:after', (e, row, data) => {
        var monlist = new twentyc.rest.List(
          $ctl.template("asn_monitor_list")
        );
        monlist.element.find('a[data-action="add_monitor"]').click(() => {
          this.prompt_add_asn_monitor(row.data("apiobject"))
        });


        monlist.formatters.status = $ctl.formatters.monitor_status;
        monlist.base_url = monlist.base_url.replace("/0", "/"+data.id);
        monlist.local_action('edit_asn_monitor', (asn_monitor, _row) => {
          this.prompt_edit_asn_monitor(
            row.data('apiobject'), asn_monitor
          );
        });

        $(monlist).on("load:after", () => {
          if(monlist.list_body.find('.row').length > 0) {
            monlist.element.find('div.list-empty').hide();
          } else {
            monlist.element.find('div.list-empty').show();
          }
        });

        monlist.load().then(() => {
          monlist.element.appendTo(row.children('td.monitors').last());
        });
        row.data("monlist", monlist);
      });


      $(this.$w.list).on('remove:before', (e, data) => {
        this.collapse_asns(data);
      });
      this.$w.list.element.find('[data-element="button_add_asn_set"]').click(() => {
        this.prompt_add_asn_set();
      });


    },

    prompt_add_asn_set : function() {
      return new $ctl.application.Prefixctl.ModalASNSet();
    },

    prompt_edit_asn_set : function(asn_set) {
      return new $ctl.application.Prefixctl.ModalASNSet(asn_set);
    },

    prompt_add_asn_monitor : function(asn_set) {
      return new $ctl.application.Prefixctl.ModalASNMonitor(asn_set);
    },

    prompt_edit_asn_monitor : function(asn_set, asn_monitor) {
      return new $ctl.application.Prefixctl.ModalASNMonitor(asn_set, asn_monitor);
    },

    asns_expanded : function(asn_set) {
      return this.elements.body.find('#asns-'+asn_set.id).length > 0
    },

    toggle_asns : function(asn_set, row) {
      if(this.asns_expanded(asn_set)) {
        this.collapse_asns(asn_set);
      } else {
        this.expand_asns(asn_set, row);
      }
    },

    expand_asns : function(asn_set, row) {
      if(this.asns_expanded(asn_set))
        return;

      if(row.length > 1) {
        row = row.first()
      }

      const list = new twentyc.rest.List(
        this.template('asns_list')
      );
      list.base_url = list.base_url.replace("/0", "/"+asn_set.id);
      list.element.insertAfter(row);
      list.load();

      const form = new $ctl.application.Prefixctl.ASNtoASNSetForm(
        list.element.find('.controls > form')
      )
      form.base_url = form.base_url.replace("/0", "/"+asn_set.id);
      form.element.find("span.select2:nth-of-type(2)").last().remove()
      $(form).on('api-write:success', () => { list.load() });
      list.element.attr('id', 'asns-'+asn_set.id)
    },

    collapse_asns : function(asn_set) {
      const node = this.elements.body.find('#asns-'+asn_set.id)
      node.remove()
    },


    menu : function() {
      let menu = this.Tool_menu();
      menu.find('[data-element="button_add_asn_set"]').click(() => {
        this.prompt_add_asn_set();
      });

      $(this.delete_selected_button).insertBefore(menu.find('[data-element="button_add_asn_set"]'));
      $(this.delete_selected_button).click(() => {
        if (confirm("Remove selected ASN Sets?")) {
          this.$w.list.delete_selected_list();
        }
      });

      return menu;
    },

    // v2 - add bottom menu
    bottom_menu : function() {
      let bottom_menu = this.Tool_bottom_menu();
      bottom_menu.find('[data-element="button_api_view"]').attr(
        "href", this.$w.list.base_url + "/?pretty"
      )

      return bottom_menu;
    },

    activate : function() {
      this.$w.list.load();
      return this.Tool_activate();
    }
  },
  $ctl.application.Tool
);

$ctl.application.Prefixctl.ASNtoASNSetForm = $tc.extend(
  "ASNtoASNSetForm",
  {
    ASNtoASNSetForm : function(jq) {
      this.Form(jq);
    },

    render_non_field_errors : function(errors) {
      const index = errors.indexOf("The fields asn_set, asn must make a unique set.");
      if (index > -1) {
        errors.splice(index, 1);
        errors.push("This ASN already exists in the set.");
      }

      return this.Form_render_non_field_errors(errors);
    },
  },
  twentyc.rest.Form
);


$ctl.application.Prefixctl.ModalASNSet = $tc.extend(
  "ModalASNSet",
  {
    ModalASNSet : function(asn_set) {
      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_asn_set")
      );

      var modal = this;
      var title = "Add ASN Set";

      if(asn_set) {
        form.fill(asn_set);
        form.method = "PUT"
        form.form_action = asn_set.id
        title = "Edit ASN Set";
      }

      $(this.form).on(
        "api-write:success",
        function(event, endpoint, payload, response) {
          var list = $ctl.prefixctl.$t.asn_sets.$w.list;
          list.load().then(() => {
            $ctl.prefixctl.$t.asn_sets.expand_asns(response.first())
          });
          modal.hide();
        }
      );
      this.Modal("save_right", title, form.element);
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
)


$ctl.application.Prefixctl.ModalASNMonitor = $tc.extend(
  "ModalASNMonitor",
  {
    ModalASNMonitor : function(asn_set, asn_monitor) {
      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_asn_monitor")
      );

      var modal = this;
      var title = asn_set.name + ": Add Monitor"

      if(asn_monitor) {
        form.fill(asn_monitor)
        form.form_action = asn_monitor.id
        form.method = "PUT";
        title = asn_set.name + ": Edit Monitor"
      }

      $(this.form).on(
        "api-write:before",
        function(event, endpoint, payload, method) {
          payload.asn_set = asn_set.id;
        }
      );

      $(this.form).on(
        "api-write:success",
        function(event, endpoint, payload, response) {
          var row = $ctl.prefixctl.$t.asn_sets.$w.list.find_row(
            asn_set.id
          );
          row.filter('tr.secondary').show();
          row.data("monlist").load();
          modal.hide();
        }
      );


      this.Modal("save", title, form.element);
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
)



$(document).ready(function() {
  $ctl.prefixctl = new $ctl.application.Prefixctl();
});

})(jQuery, twentyc.cls, fullctl);
