# Copyright © 2021 rdbende <rdbende@gmail.com>

source [file join [file dirname [info script]] create_azure_theme.tcl]

namespace eval ttk::theme::azure-light {
    variable version 2.0
    package provide ttk::theme::azure-light $version

    ttk::style theme create azure-light -parent clam -settings {
        create_azure_theme light
    }
}
