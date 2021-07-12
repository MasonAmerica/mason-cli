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

// deployConfigCmd represents the deployConfig command
var deployConfigCmd = &cobra.Command{
	Use:   "config",
	Short: "",
	Long:  ``,
	Run:   deployConfig,
}

func init() {
	rootCmd.AddCommand(deployConfigCmd)
	deployConfigCmd.Flags().BoolVarP(&await, "await", "", false, "")

	deployConfigCmd.Flags().BoolVarP(&assumeYes, "assume-yes", "", false, "")
	deployConfigCmd.Flags().BoolVarP(&assumeYes, "yes", "y", false, "")
	deployConfigCmd.Flags().BoolVarP(&dryRun, "dry-run", "", false, "")
	deployConfigCmd.Flags().BoolVarP(&push, "push", "p", false, "")
	deployConfigCmd.Flags().BoolVarP(&noHTTPS, "no-https", "", false, "")
	deployConfigCmd.Flags().BoolVarP(&skipVerify, "skip-verify", "", false, "")
	deployConfigCmd.Flags().BoolVarP(&turbo, "turbo", "", false, "")
	deployConfigCmd.Flags().BoolVarP(&noTurbo, "no-turbo", "", false, "")
	deployConfigCmd.Flags().StringVarP(&masonVersion, "mason-version", "", "", "")

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// deployConfigCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// deployConfigCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func deployConfig(cmd *cobra.Command, args []string) {
	passThroughArgs := make([]string, 0)
	passThroughArgs = append(passThroughArgs, "deploy")
	passThroughArgs = append(passThroughArgs, "config")
	passThroughArgs = append(passThroughArgs, args...)
	getFlags(cmd, passThroughArgs, deployFlags)

	Passthrough(passThroughArgs...)
}
