package main

import (
	"fmt"
	"strconv"
	"time"
)

type IPFSData struct {
	Hash string
	Key  string
}

type Post struct {
	Alias     string
	Title     string
	Content   string
	Timestamp string
	IPFSData
}

type Comment struct {
	Post      string
	Parent    string
	Alias     string
	Content   string
	Timestamp string
	IPFSData
}

func Now() string {
	return strconv.FormatInt(time.Now().Unix(), 10)
}

func main() {
	MyCurator.Init()
	post := Post{
		"hautonjt",
		"Hello World!",
		"Hi guys",
		Now(),
		IPFSData{
			"abc",
			"def",
		},
	}

	comment := Comment{
		"abc",
		"abc",
		"hautonjt",
		"Hello from comment!",
		Now(),
		IPFSData{
			"ghi",
			"def",
		},
	}

	res := MyCurator.OnPostAdded(&post, false)
	fmt.Println("Test 1 Passed")

	post.Hash = "qwer"
	res = MyCurator.OnPostAdded(&post, true)
	if res {
		fmt.Println("Test 2 Passed")
	} else {
		fmt.Println("Test 2 Failed")
	}

	res = MyCurator.OnCommentAdded(&comment, false)
	fmt.Println("Test 3 Passed")

	comment.Hash = "qiweop"
	res = MyCurator.OnCommentAdded(&comment, true)
	if res {
		fmt.Println("Test 4 Passed")
	} else {
		fmt.Println("Test 4 Failed")
	}
	hashList := MyCurator.GetContent(make(map[string]interface{}))
	if len(hashList) == 2 {
		fmt.Println("Test 5 Passed")
	} else {
		fmt.Println("Test 5 Failed")
	}

	MyCurator.FlagContent("abc", true)
	hashList = MyCurator.GetContent(make(map[string]interface{}))
	if hashList[0] != "abc" {
		fmt.Println("Test 6 Passed")
	} else {
		fmt.Println("Test 6 Failed")
	}

	MyCurator.FlagContent("abc", false)
	MyCurator.FlagContent("qwer", true)
	hashList = MyCurator.GetContent(make(map[string]interface{}))
	if hashList[0] == "abc" {
		fmt.Println("Test 7 Passed")
	} else {
		fmt.Println("Test 7 Failed")
	}

	MyCurator.FlagContent("qwer", false)
	MyCurator.UpvoteContent("abc")
	hashList = MyCurator.GetContent(make(map[string]interface{}))
	if hashList[0] == "abc" {
		fmt.Println("Test 8 Passed")
	} else {
		fmt.Println("Test 8 Failed")
	}

	MyCurator.DownvoteContent("abc")
	MyCurator.DownvoteContent("abc")
	hashList = MyCurator.GetContent(make(map[string]interface{}))
	if hashList[0] == "abc" {
		fmt.Println("Test 9 Passed")
	} else {
		fmt.Println("Test 9 Failed")
	}

	if MyCurator.Close() == nil {
		fmt.Println("Final Test Passed")
	} else {
		fmt.Println("Final Test Failed")
	}
}
