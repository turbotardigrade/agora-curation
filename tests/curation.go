package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"os/exec"
)

var MyCurator = MLCurator{}

type Curator interface {
	// Init will be called on initialization, use this function to
	// initialize your curation module
	Init() error

	// OnPostAdded will be called when new posts are retrieved
	// from other peers, if this functions returns false, the
	// content will be rejected (e.g. in the case of spam) and not
	// stored by our node
	OnPostAdded(obj *Post, isWhitelabeled bool) bool

	// OnCommentAdded will be called when new comments are
	// retrieved from other peers, if this functions returns
	// false, the content will be rejected (e.g. in the case of
	// spam) and not stored by our node
	OnCommentAdded(obj *Comment, isWhitelabeled bool) bool

	// GetContent gives back an ordered array of post hashes of
	// suggested content by the curation module
	GetContent(params map[string]interface{})

	// FlagContent marks or unmarks hashes as spam. True means
	// content is flagged as spam, false means content is not
	// flagged as spam
	FlagContent(hash string, isFlagged bool)

	// UpvoteContent is called when user upvotes a content
	UpvoteContent(hash string)

	// DownvoteContent is called when user downvotes a content
	DownvoteContent(hash string)

	Close() error
}

type Command struct {
	Id        int                    `json:"id"`
	Command   string                 `json:"command"`
	Arguments map[string]interface{} `json:"arguments"`
}

type Result struct {
	Id     int         `json:"id"`
	Result interface{} `json:"result"`
	Error  string      `json:"error"`
}

type MLCurator struct{}

var cmd *exec.Cmd
var in io.WriteCloser
var scanner *bufio.Scanner

// Init initializes boltdb which simply keeps track of saved hashes
// and their arrivaltime
func (c *MLCurator) Init() error {
	cmd = exec.Command("../dist/main")
	in, _ = cmd.StdinPipe()
	out, _ := cmd.StdoutPipe()
	scanner = bufio.NewScanner(out)
	cmd.Start()
	return nil
}

func (c *MLCurator) OnPostAdded(obj *Post, isWhitelabeled bool) bool {
	res, _ := sendCommand(Command{
		rand.Int(), "on_post_added", map[string]interface{}{
			"obj":            obj,
			"isWhitelabeled": isWhitelabeled,
		},
	})
	if res.Error == "" {
		r := res.Result.(bool)
		return r
	}
	fmt.Println("error occurred")
	return false
}

func (c *MLCurator) OnCommentAdded(obj *Comment, isWhitelabeled bool) bool {
	res, _ := sendCommand(Command{
		rand.Int(), "on_comment_added", map[string]interface{}{
			"obj":            obj,
			"isWhitelabeled": isWhitelabeled,
		},
	})
	if res.Error == "" {
		r := res.Result.(bool)
		return r
	}
	return false
}

func (c *MLCurator) GetContent(params map[string]interface{}) []string {
	res, _ := sendCommand(Command{
		rand.Int(), "get_content", map[string]interface{}{
			"params": params,
		},
	})
	if res.Error == "" {
		r := res.Result.([]interface{})
		if len(r) > 0 {
			retval := make([]string, len(r))
			for i, v := range r {
				retval[i] = v.(string)
			}
			return retval
		}
		return nil
	}
	return nil
}

func (c *MLCurator) FlagContent(hash string, isFlagged bool) {
	sendCommand(Command{
		rand.Int(), "flag_content", map[string]interface{}{
			"hash":      hash,
			"isFlagged": isFlagged,
		},
	})
}

func (c *MLCurator) UpvoteContent(hash string) {
	sendCommand(Command{
		rand.Int(), "upvote_content", map[string]interface{}{
			"hash": hash,
		},
	})
}

func (c *MLCurator) DownvoteContent(hash string) {
	sendCommand(Command{
		rand.Int(), "downvote_content", map[string]interface{}{
			"hash": hash,
		},
	})
}

func (c *MLCurator) Close() error {
	_, err := sendCommand(Command{
		rand.Int(), "quit", nil,
	})
	return err
}

func sendCommand(command Command) (*Result, error) {
	obj, err := json.Marshal(command)
	var res Result
	if err != nil {
		fmt.Println("Marshal: " + err.Error())
		res = Result{
			command.Id, nil, "Marshal: " + err.Error(),
		}
		return &res, err
	}
	_, err = io.WriteString(in, string(obj)+"\n")
	if err != nil {
		fmt.Println("I/O: " + err.Error())
		res = Result{
			command.Id, nil, "I/O: " + err.Error(),
		}
		return &res, err
	}
	for scanner.Scan() {
		if len(scanner.Text()) > 0 {
			break
		}
	}
	err = json.Unmarshal([]byte(scanner.Text()), &res)
	if err != nil {
		fmt.Println("UNMARSHAL: " + err.Error())
		res = Result{
			command.Id, nil, "I/O: " + err.Error(),
		}
		return &res, err
	}
	return &res, nil
}
