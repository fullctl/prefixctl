(function ($, $tc, $ctl) {

    /**
     * Example monitor modal, used for creating and editing example monitors
     */
    $ctl.application.Prefixctl.ModalExampleMonitor = $tc.extend(
        "ModalExampleMonitor",
        {
            ModalExampleMonitor: function (prefix_set, monitor) {
                // set properties
                this.prefix_set = prefix_set;
                this.monitor = monitor;
                this.name = "example_monitor";

                // get a form instance for the monitor set up form
                this.init_form(monitor);

                // init example monitor as a prefix-set monitor
                this.init_prefix_set_monitor()
            }
        },

        // extend from base monitor class
        $ctl.application.Prefixctl.ModalMonitorBase
    )

    // register the monitor
    $ctl.application.Prefixctl.PrefixSetMonitors.register(
        {
            // same as django model handle-ref tag
            name: "example_monitor",
            // what namespaces does the viewing user need to be permissioned
            // to to view this monitor
            permissions: ["prefix_monitor"],
            // what is the display name of the monitor
            label: "Example Monitor",
            // function that opens the monitor modal for creation or editing
            modal: function (prefix_set, monitor) {
                return new $ctl.application.Prefixctl.ModalExampleMonitor(prefix_set, monitor);
            }
        }
    );

})(jQuery, twentyc.cls, fullctl);