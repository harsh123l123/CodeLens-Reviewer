package main

import (
	"fmt"
	"net/http"
	"time"
)

// Global map accessed concurrently without sync.RWMutex
var sessionStore = make(map[string]string)

func handleLogin(w http.ResponseWriter, r *http.Request) {
	userId := r.URL.Query().Get("user_id")
	token := r.URL.Query().Get("token")

	// DATA RACE: Unsynchronized map write in concurrent HTTP handler
	go func() {
		sessionStore[userId] = token
		time.Sleep(100 * time.Millisecond)
		fmt.Printf("User %s logged in\n", userId)
	}()

	w.Write([]byte("Logged in successfully"))
}

func handleGetSession(w http.ResponseWriter, r *http.Request) {
	userId := r.URL.Query().Get("user_id")
	// DATA RACE: Unsynchronized map read while goroutine may write
	token := sessionStore[userId]
	w.Write([]byte(token))
}

func main() {
	http.HandleFunc("/login", handleLogin)
	http.HandleFunc("/session", handleGetSession)
	http.ListenAndServe(":8080", nil)
}
