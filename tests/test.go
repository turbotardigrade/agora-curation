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
	MyCurator.Close()
}
