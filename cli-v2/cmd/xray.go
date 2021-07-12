/*
Copyright © 2021 Mason support@bymason.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

// NOTE: VNC is known as desktop to customers

// xrayCmd represents the xray command
var xrayCmd = &cobra.Command{
	Use:   "xray",
	Short: "",
	Long:  ``,
	Run:   xrayCommand,
}

func init() {
	rootCmd.AddCommand(xrayCmd)
	xrayCmd.AddCommand(pullCmd)
	xrayCmd.AddCommand(pushCmd)
	xrayCmd.AddCommand(pullCmd)
	xrayCmd.AddCommand(installCmd)
	xrayCmd.AddCommand(uninstallCmd)
	xrayCmd.AddCommand(adbproxyCmd)
	xrayCmd.AddCommand(vncCmd)
	xrayCmd.AddCommand(bugreportCmd)
	xrayCmd.AddCommand(logcatCmd)
	xrayCmd.AddCommand(screencapCmd)

	var port string
	xrayCmd.Flags().StringVarP(&port, "port", "p", "", "")
	xrayCmd.Flags().StringVarP(&port, "output", "o", "", "")

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// xrayCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// xrayCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func xrayCommand(cmd *cobra.Command, args []string) {
	if len(args) < 2 {
		fmt.Println("Must provide valid device ID and xray command")
		return
	}

	passthroughArgs := make([]string, 0)
	passthroughArgs = getFlags(cmd, passthroughArgs, persistentFlags)
	passthroughArgs = append(passthroughArgs, args...)

	deviceID := args[0]
	subcommand := args[1]

	additionalArgs := make([]string, 0)
	if len(args) > 2 {
		additionalArgs = args[2:]
	}

	subArgs := append([]string{deviceID}, additionalArgs...)
	parseXrayCommand(cmd, subcommand, subArgs, passthroughArgs)
}

func parseXrayCommand(cmd *cobra.Command, subcmd string, args []string, passthroughArgs []string) {
	switch subcmd {
	case "pull":
		pullCmd.Run(cmd, args)
	case "push":
		pushCmd.Run(cmd, args)
	case "install":
		installCmd.Run(cmd, args)
	case "uninstall":
		uninstallCmd.Run(cmd, args)
	case "adbproxy":
		adbproxyCmd.Run(cmd, args)
	case "bugreport":
		bugreportCmd.Run(cmd, args)
	case "screencap":
		screencapCmd.Run(cmd, args)
	case "logcat":
		logcatCmd.Run(cmd, args)
	case "desktop":
		logcatCmd.Run(cmd, args)
	default:
		Passthrough(passthroughArgs...)
	}
}
