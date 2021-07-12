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
	"fmt"
	"os"
	"os/exec"

	"github.com/spf13/cobra"

	homedir "github.com/mitchellh/go-homedir"
	"github.com/spf13/viper"
)

// global flags available on every legacy command
var persistentFlags = []passthroughFlag{
	NewPassthroughFlag("token", "t"),
	NewPassthroughFlag("version", ""),
	NewPassthroughFlag("api-key", ""),
	NewPassthroughFlag("debug", "d"),
	NewPassthroughFlag("verbosity", "v"),
}

var cfgFile string
var apiKeyRoot string
var token string
var version bool

var sub = &cobra.Command{}

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "cli-v2",
	Short: "",
	Long:  ``,
	// Uncomment the following line if your bare application
	// has an action associated with it:
	Run: func(cmd *cobra.Command, args []string) {
		// placeholder command for sub commands
		Passthrough("")
	},
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	cobra.CheckErr(rootCmd.Execute())
}

func init() {
	cobra.OnInitialize(initConfig)

	// Here you will define your flags and configuration settings.
	// Cobra supports persistent flags, which, if defined here,
	// will be global for your application.

	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.cli-v2.yaml)")
	rootCmd.PersistentFlags().BoolVarP(&version, "version", "V", false, "")
	rootCmd.PersistentFlags().StringVarP(&apiKeyRoot, "api-key", "", "", "")
	rootCmd.PersistentFlags().StringVarP(&token, "token", "t", "", "")
	rootCmd.PersistentFlags().StringVarP(&token, "access-token", "", "", "")
	rootCmd.PersistentFlags().StringVarP(&token, "id-token", "", "", "")
	rootCmd.PersistentFlags().StringVarP(&token, "no-color", "", "", "")
	rootCmd.PersistentFlags().StringVarP(&token, "debug", "d", "", "")
	rootCmd.PersistentFlags().StringVarP(&token, "verbose", "", "", "")
	rootCmd.PersistentFlags().StringVarP(&token, "verbosity", "v", "", "")

	// Cobra also supports local flags, which will only run
	// when this action is called directly.
	//rootCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

// initConfig reads in config file and ENV variables if set.
func initConfig() {
	if cfgFile != "" {
		// Use config file from the flag.
		viper.SetConfigFile(cfgFile)
	} else {
		// Find home directory.
		home, err := homedir.Dir()
		cobra.CheckErr(err)

		// Search config in home directory with name ".cli-v2" (without extension).
		viper.AddConfigPath(home)
		viper.SetConfigName(".cli-v2")
	}

	viper.AutomaticEnv() // read in environment variables that match

	// If a config file is found, read it in.
	if err := viper.ReadInConfig(); err == nil {
		fmt.Fprintln(os.Stderr, "Using config file:", viper.ConfigFileUsed())
	}
}

// Pass command to CLI-V1
func Passthrough(sub ...string) {
	root := "mason"
	cmd := exec.Command(root, sub...)
	cmd.Stdout = os.Stdout
	cmd.Stdin = os.Stdin
	cmd.Stderr = os.Stderr
	err := cmd.Run()
	if err != nil {
		fmt.Println(fmt.Sprintf("Command failed: %s", err.Error()))
	}
}

type passthroughFlag struct {
	name      string
	shorthand string
}

func NewPassthroughFlag(name, shorthand string) passthroughFlag {
	return passthroughFlag{name: name, shorthand: shorthand}
}

// Get flags parses a cobra command for its flags, converts them to strings
// and appends them to the command string we pass to the python CLI
func getFlags(c *cobra.Command, passThroughArgs []string, flags []passthroughFlag) []string {
	for _, f := range flags {

		// throw away error here because we are iterating over each flag and checking for a value
		// even if that flag hasn't been provided in the cli command
		b, _ := c.Flags().GetBool(f.name)
		if b {
			if f.shorthand != "" {
				passThroughArgs = append(passThroughArgs, "-"+f.shorthand)
			} else {
				passThroughArgs = append(passThroughArgs, "--"+f.name)
			}
			continue
		}

		// throw away errors for the same reason as above
		s, _ := c.Flags().GetString(f.name)
		if len(s) > 0 {
			if f.shorthand != "" {
				passThroughArgs = append(passThroughArgs, "-"+f.shorthand)
			} else {
				passThroughArgs = append(passThroughArgs, "--"+f.name)
			}

			passThroughArgs = append(passThroughArgs, s)
		}
	}
	return passThroughArgs
}

func GetFlags(c *cobra.Command, pt []string, flags []passthroughFlag) []string {
	pt = getFlags(c, pt, flags)
	pt = getFlags(rootCmd, pt, persistentFlags)
	return pt
}
