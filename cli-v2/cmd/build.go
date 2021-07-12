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

// buildCmd represents the build command
var buildCmd = &cobra.Command{
	Use:   "build",
	Short: "",
	Long:  ``,
	Run:   build,
}

func init() {
	rootCmd.AddCommand(buildCmd)
	buildCmd.Flags().BoolVarP(&await, "await", "", false, "")
	buildCmd.Flags().BoolVarP(&turbo, "turbo", "", false, "")
	buildCmd.Flags().BoolVarP(&noTurbo, "no-turbo", "", false, "")
	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// buildCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// buildCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

var buildFlags = []passthroughFlag{
	NewPassthroughFlag("await", ""),
	NewPassthroughFlag("turbo", ""),
	NewPassthroughFlag("no-turbo", ""),
}

func build(cmd *cobra.Command, args []string) {
	passthroughArgs := make([]string, 0)
	passthroughArgs = append(passthroughArgs, "build")
	passthroughArgs = append(passthroughArgs, args...)
	getFlags(cmd, passthroughArgs, buildFlags)
	Passthrough(passthroughArgs...)
}
