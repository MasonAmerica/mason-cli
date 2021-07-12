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

// stageCmd represents the stage command
var stageCmd = &cobra.Command{
	Use:   "stage",
	Short: "",
	Long:  ``,
	Run:   stage,
}

func init() {
	rootCmd.AddCommand(stageCmd)
	stageCmd.Flags().Bool("yes", false, "")
	stageCmd.Flags().BoolVarP(&assumeYes, "assume-yes", "", false, "")
	stageCmd.Flags().BoolVarP(&turbo, "turbo", "", false, "")
	stageCmd.Flags().BoolVarP(&noTurbo, "no-turbo", "", false, "")
	stageCmd.Flags().StringVarP(&masonVersion, "mason-version", "", "", "")
	stageCmd.Flags().BoolVarP(&skipVerify, "skip-verify", "s", false, "")

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// stageCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// stageCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

var stageFlags = []passthroughFlag{
	NewPassthroughFlag("assume-yes", ""),
	NewPassthroughFlag("yes", "y"),
	NewPassthroughFlag("turbo", ""),
	NewPassthroughFlag("no-turbo", ""),
	NewPassthroughFlag("mason.verion", ""),
	NewPassthroughFlag("skip-verify", "s"),
}

func stage(cmd *cobra.Command, args []string) {
	passthroughArgs := make([]string, 0)
	passthroughArgs = append(passthroughArgs, "stage")
	GetFlags(cmd, passthroughArgs, stageFlags)
	passthroughArgs = append(passthroughArgs, args...)
	Passthrough(passthroughArgs...)
}
