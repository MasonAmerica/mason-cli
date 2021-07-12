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
	"github.com/spf13/cobra"
)

// registerMediaBootanimationCmd represents the registerMediaBootanimation command
var registerMediaBootanimationCmd = &cobra.Command{
	Use:   "bootanimation",
	Short: "",
	Long:  ``,
	Run:   registerMediaBootanimation,
}

func init() {
	rootCmd.AddCommand(registerMediaBootanimationCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// registerMediaBootanimationCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// registerMediaBootanimationCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func registerMediaBootanimation(cmd *cobra.Command, args []string) {
	passThroughArgs := make([]string, 0)
	passThroughArgs = append(passThroughArgs, []string{"register", "media", "bootanimation"}...)
	passThroughArgs = append(passThroughArgs, args...)
	Passthrough(passThroughArgs...)
}
