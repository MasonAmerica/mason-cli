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

// deployApkCmd represents the deployApk command
var deployApkCmd = &cobra.Command{
	Use:   "apk",
	Short: "",
	Long:  ``,
	Run:   deployApk,
}

func init() {
	rootCmd.AddCommand(deployApkCmd)

	deployApkCmd.Flags().BoolVarP(&assumeYes, "assume-yes", "", false, "")
	deployApkCmd.Flags().BoolVarP(&assumeYes, "yes", "y", false, "")
	deployApkCmd.Flags().BoolVarP(&dryRun, "dry-run", "", false, "")
	deployApkCmd.Flags().BoolVarP(&push, "push", "p", false, "")
	deployApkCmd.Flags().BoolVarP(&noHTTPS, "no-https", "", false, "")
	deployApkCmd.Flags().BoolVarP(&skipVerify, "skip-verify", "", false, "")
	deployApkCmd.Flags().BoolVarP(&turbo, "turbo", "", false, "")
	deployApkCmd.Flags().BoolVarP(&noTurbo, "no-turbo", "", false, "")
	deployApkCmd.Flags().StringVarP(&masonVersion, "mason-version", "", "", "")
	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// deployApkCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// deployApkCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func deployApk(cmd *cobra.Command, args []string) {
	passThroughArgs := make([]string, 0)
	passThroughArgs = append(passThroughArgs, "deploy")
	passThroughArgs = append(passThroughArgs, "apk")
	passThroughArgs = append(passThroughArgs, args...)
	passThroughArgs = GetFlags(cmd, passThroughArgs, deployFlags)
	Passthrough(passThroughArgs...)
}
