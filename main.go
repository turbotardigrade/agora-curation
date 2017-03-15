package main

import (
	"encoding/json"
	"io"
	"os"
	"os/exec"
)

type Command struct {
	Id        int               `json:"id"`
	Command   string            `json:"command"`
	Arguments map[string]string `json:"arguments"`
}

func main() {
	m := make(map[string]string)
	m["data"] = "42a"
	command := Command{
		1, "hello", m,
	}
	cmd := exec.Command("./dist/main/main")
	in, _ := cmd.StdinPipe()
	cmd.Stdout = os.Stdout
	cmd.Start()
	defer cmd.Wait()
	res, _ := json.Marshal(command)
	io.WriteString(in, string(res))
}
