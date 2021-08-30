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

// vncCmd represents the vnc command
var vncCmd = &cobra.Command{
	Use:   "vnc",
	Short: "",
	Long:  ``,
	Run:   vnc,
}

func init() {
	rootCmd.AddCommand(vncCmd)
	vncCmd.Flags().StringVarP(&portFlag, "port", "p", "", "")

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// vncCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// vncCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func vnc(cmd *cobra.Command, args []string) {
	if len(args) < 1 {
		fmt.Println("Must provide valid device ID")
		return
	}

	passthroughArgs := make([]string, 0)
	passthroughArgs = append(passthroughArgs, "xray")
	deviceID := args[0]
	passthroughArgs = append(passthroughArgs, deviceID)
	passthroughArgs = append(passthroughArgs, "desktop")
	passthroughArgs = append(passthroughArgs, args[1:]...)
	Passthrough(passthroughArgs...)
}
