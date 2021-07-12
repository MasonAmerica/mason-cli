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

// deployCmd represents the deploy command
var deployCmd = &cobra.Command{
	Use:   "deploy",
	Short: "",
	Long:  ``,
	Run:   deploy,
}

func init() {
	rootCmd.AddCommand(deployCmd)
	deployCmd.Flags().BoolVarP(&assumeYes, "assume-yes", "", false, "")
	deployCmd.Flags().BoolVarP(&assumeYes, "yes", "y", false, "")
	deployCmd.Flags().BoolVarP(&push, "push", "p", false, "")
	deployCmd.Flags().BoolVarP(&noHTTPS, "no-https", "", false, "")
	deployCmd.Flags().BoolVarP(&skipVerify, "skip-verify", "", false, "")
	deployCmd.Flags().BoolVarP(&turbo, "turbo", "", false, "")
	deployCmd.Flags().BoolVarP(&noTurbo, "no-turbo", "", false, "")

	deployCmd.Flags().BoolP("dry-run", "", false, "")

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// deployCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// deployCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

var deployFlags = []passthroughFlag{
	NewPassthroughFlag("assume-yes", ""),
	NewPassthroughFlag("dry-run", ""),
	NewPassthroughFlag("push", "p"),
	NewPassthroughFlag("no-https", ""),
	NewPassthroughFlag("yes", "y"),
	NewPassthroughFlag("skip-verify", "s"),
	NewPassthroughFlag("turbo", ""),
	NewPassthroughFlag("no-turbo", ""),
}

func deploy(cmd *cobra.Command, args []string) {
	passthroughArgs := make([]string, 0)
	passthroughArgs = append(passthroughArgs, "deploy")
	passthroughArgs = getFlags(cmd, passthroughArgs, deployFlags)
	Passthrough(passthroughArgs...)
}
