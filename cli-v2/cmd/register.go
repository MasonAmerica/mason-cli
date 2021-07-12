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

// registerCmd represents the register command
var registerCmd = &cobra.Command{
	Use:   "register",
	Short: "",
	Long:  ``,
	Run:   register,
}

func init() {
	rootCmd.AddCommand(registerCmd)
	registerCmd.AddCommand(registerApkCmd)
	registerCmd.AddCommand(registerConfigCmd)
	registerCmd.AddCommand(registerProjectCmd)
	registerCmd.AddCommand(registerMediaCmd)

	registerCmd.PersistentFlags().BoolVarP(&assumeYes, "assume-yes", "", false, "")
	registerCmd.PersistentFlags().BoolVarP(&assumeYes, "yes", "", false, "")
	registerCmd.PersistentFlags().BoolVarP(&dryRun, "dry-run", "", false, "")
	registerCmd.PersistentFlags().BoolVarP(&skipVerify, "skip-verify", "s", false, "")
	registerCmd.PersistentFlags().BoolVarP(&await, "await", "", false, "")
	registerCmd.PersistentFlags().BoolVarP(&turbo, "turbo", "", false, "")
	registerCmd.PersistentFlags().BoolVarP(&noTurbo, "no-turbo", "", false, "")
	registerCmd.PersistentFlags().StringVarP(&masonVersion, "mason-version", "", "", "")

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// registerCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// registerCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

var registerFlags = []passthroughFlag{
	NewPassthroughFlag("assume-yes", ""),
	NewPassthroughFlag("yes", "y"),
	NewPassthroughFlag("dry-run", ""),
	NewPassthroughFlag("skip-verify", "s"),
	NewPassthroughFlag("await", ""),
	NewPassthroughFlag("turbo", ""),
	NewPassthroughFlag("no-turbo", ""),
	NewPassthroughFlag("mason-version", ""),
}

func register(cmd *cobra.Command, args []string) {
	passthroughArgs := make([]string, 0)
	passthroughArgs = append(passthroughArgs, "register")
	passthroughArgs = append(passthroughArgs, args...)
	Passthrough(passthroughArgs...)
}
