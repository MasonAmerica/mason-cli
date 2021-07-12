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

// loginCmd represents the login command
var loginCmd = &cobra.Command{
	Use:   "login",
	Short: "",
	Long:  ``,
	Run:   login,
}

func init() {
	rootCmd.AddCommand(loginCmd)

	loginCmd.Flags().StringVarP(&username, "username", "", "", "")
	loginCmd.Flags().StringVarP(&username, "user", "u", "", "")
	loginCmd.Flags().StringVarP(&password, "password", "p", "", "")
	loginCmd.Flags().StringVarP(&username, "pass", "", "", "")
	loginCmd.Flags().StringVarP(&apiKey, "token", "t", "", "")

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// loginCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// loginCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

var loginFlags = []passthroughFlag{
	NewPassthroughFlag("username", ""),
	NewPassthroughFlag("user", ""),
	NewPassthroughFlag("password", "p"),
	NewPassthroughFlag("pass", ""),
	NewPassthroughFlag("token", "t"),
}

func login(cmd *cobra.Command, args []string) {
	passThroughArgs := make([]string, 0)
	passThroughArgs = append(passThroughArgs, "login")
	passThroughArgs = append(passThroughArgs, args...)
	passThroughArgs = GetFlags(cmd, passThroughArgs, loginFlags)
	Passthrough(passThroughArgs...)
}
