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

// registerConfigCmd represents the registerConfig command
var registerConfigCmd = &cobra.Command{
	Use:   "config",
	Short: "",
	Long:  ``,
	Run:   registerConfig,
}

func init() {
	rootCmd.AddCommand(registerConfigCmd)
	registerConfigCmd.Flags().BoolVarP(&assumeYes, "assume-yes", "", false, "")
	registerConfigCmd.Flags().BoolVarP(&assumeYes, "yes", "", false, "")
	registerConfigCmd.Flags().BoolVarP(&dryRun, "dry-run", "", false, "")
	registerConfigCmd.Flags().BoolVarP(&skipVerify, "skip-verify", "s", false, "")
	registerConfigCmd.Flags().BoolVarP(&await, "await", "", false, "")
	registerConfigCmd.Flags().BoolVarP(&turbo, "turbo", "", false, "")
	registerConfigCmd.Flags().BoolVarP(&noTurbo, "no-turbo", "", false, "")
	registerConfigCmd.Flags().StringVarP(&masonVersion, "mason-version", "", "", "")
	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// registerConfigCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// registerConfigCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func registerConfig(cmd *cobra.Command, args []string) {
	passThroughArgs := make([]string, 0)
	passThroughArgs = append(passThroughArgs, "register")
	passThroughArgs = append(passThroughArgs, "config")
	passThroughArgs = append(passThroughArgs, args...)
	GetFlags(cmd, passThroughArgs, registerFlags)
	Passthrough(passThroughArgs...)
}
