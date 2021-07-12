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

// debugCmd represents the debug command
var debugCmd = &cobra.Command{
	Use:   "debug",
	Short: "",
	Long:  ``,
	Run:   debug,
}

func init() {
	rootCmd.AddCommand(debugCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// debugCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// debugCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func debug(cmd *cobra.Command, args []string) {
	passthroughArgs := make([]string, 0)
	version, err := rootCmd.Flags().GetString("version")
	if err != nil {
		fmt.Println(fmt.Sprintf(`
			The CLI encountered an error if this persists, please contact mason support: %s
		`, err))
	}

	if version != "" {
		passthroughArgs = append(passthroughArgs, version)
	}

	passthroughArgs = append(passthroughArgs, "debug")
	passthroughArgs = append(passthroughArgs, args...)

	Passthrough(passthroughArgs...)
}
