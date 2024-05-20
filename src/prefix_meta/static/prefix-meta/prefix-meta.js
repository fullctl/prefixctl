(function($, $tc, $ctl) {

$ctl.application.Prefixctl.Meta = $tc.extend(
  "Meta",
  {
    Meta : function(jq, prefix_set) {
      this.Button(jq);
      this.prefix_set = prefix_set;
    },

    payload : function() {
      return { "prefix_set":  this.prefix_set.id };
    }
  },
  twentyc.rest.Button
);

$(fullctl.application).on("prefixctl-ready", function(ev, app, id) {
  const prefix_sets = app.$t.prefix_sets.$w.list;

  $(prefix_sets).on("prefix-addon-controls", (e, container, data, row) => {
    const icon = $(
      '<button title="Location report" class="border-0" type="button">' +
        '<span class="inline-addon-control"><span class="icon prefixctl icon-location"></span>' +
      '</button>'
    );

    icon.click(()=> {
      new $ctl.application.Prefixctl.LocationReport(data.prefix);
    });

    container.append(icon);
  });

});

$ctl.application.Prefixctl.LocationReport = $tc.extend(
  "LocationReport",
  {
    LocationReport : function(prefix) {
      var widget = this;
      var title = "Locations - "+prefix;
      var element = $('<div>');

      var list = new twentyc.rest.List(
        $ctl.template('location_report_list')
      );

      this.list = list;

      var parts = prefix.split("/");

      var button_export = list.element.find('[data-element="button_export"]')

      button_export.attr("href", button_export.attr("href").replace(/__ip__/, parts[0]).replace(/__masklen__/, parts[1]));

      list.format_request_url = (url, method) => {
        return url.replace(/__ip__/, parts[0]).replace(/__masklen__/, parts[1]);
      };

      list.formatters.geo = (value, data) => {
        return $('<a>').attr('target', '_blank').attr('href', 'https://maps.google.com/?q='+value.latitude+','+value.longitude).text("Google Maps");
      };

      list.formatters.data = (value, data) => {
        var k, node = $('<div>');
        for(k in data.data) {
          node.append($('<span class="tag">').append(
            $('<span class="tag-name">').text(k),
            $('<span class="tag-value">').text(data.data[k])
          ));
        }
        return node;
      };

      list.formatters.row = (row, data) => {
      };

      list.load_until_data(3000, () => {
        return list.element.is(":visible");
      });

      list.element.find('.list-no-data td').append(fullctl.loading_animation());

      element.append(list.element);

      this.Modal("no_button_xl", title, element);
    },


  },
  $ctl.application.Modal
);


})(jQuery, twentyc.cls, fullctl);
