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

// registerMediaCmd represents the registerMedia command
var registerMediaCmd = &cobra.Command{
	Use:   "media",
	Short: "",
	Long:  ``,
	Run:   registerMedia,
}

func init() {
	rootCmd.AddCommand(registerMediaCmd)
	registerMediaCmd.AddCommand(registerMediaBootanimationCmd)
	registerMediaCmd.AddCommand(registerMediaSplashCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// mediaCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// mediaCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func registerMedia(cmd *cobra.Command, args []string) {
	passthroughArgs := make([]string, 0)
	passthroughArgs = getFlags(cmd, passthroughArgs, persistentFlags)
	passthroughArgs = append(passthroughArgs, []string{"register", "media"}...)
	passthroughArgs = append(passthroughArgs, args...)
	Passthrough(passthroughArgs...)
}
