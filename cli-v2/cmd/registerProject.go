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

// registerProjectCmd represents the registerProject command
var registerProjectCmd = &cobra.Command{
	Use:   "project",
	Short: "",
	Long:  ``,
	Run:   registerProject,
}

func init() {
	rootCmd.AddCommand(registerProjectCmd)
	registerProjectCmd.Flags().BoolVarP(&assumeYes, "assume-yes", "", false, "")
	registerProjectCmd.Flags().BoolVarP(&assumeYes, "yes", "", false, "")
	registerProjectCmd.Flags().BoolVarP(&dryRun, "dry-run", "", false, "")
	registerProjectCmd.Flags().BoolVarP(&skipVerify, "skip-verify", "s", false, "")
	registerProjectCmd.Flags().BoolVarP(&await, "await", "", false, "")
	registerProjectCmd.Flags().BoolVarP(&turbo, "turbo", "", false, "")
	registerProjectCmd.Flags().BoolVarP(&noTurbo, "no-turbo", "", false, "")
	registerProjectCmd.Flags().StringVarP(&masonVersion, "mason-version", "", "", "")
	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// registerProjectCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// registerProjectCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func registerProject(cmd *cobra.Command, args []string) {
	passthroughArgs := make([]string, 0)
	passthroughArgs = append(passthroughArgs, []string{"register", "project"}...)
	passthroughArgs = append(passthroughArgs, args...)
	GetFlags(cmd, passthroughArgs, registerFlags)
	Passthrough(passthroughArgs...)
}
