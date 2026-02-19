import { useEffect, useRef, useCallback } from 'react';

// KNOW AI API Connection & Usage Interface for Client Side
export const useKnowAI = (URL,endPoint, onMessage) => {
    const socket = useRef(null);

    useEffect(() => {

        //Create a connection to server 
        socket.current = new WebSocket(URL+endPoint);

        // Verbose for debugging
        socket.current.onopen = () => {
            //console.log('WebSocket connected');
        };

        // Listent to messages recieved from server 
        socket.current.onmessage = ({ data }) => {
            try {
                //Parse JSON String from server into JSON Object 
                const message = JSON.parse(data); 
                //If Handling Function Available in Call Transfer Message to it
                onMessage?.(message); 
            } 
            catch (err) {
                console.error('Failed to parse message:', err);
            }
        };

        // Verbose for debugging
        socket.current.onerror = (err) => {
            //console.error('WebSocket error:', err);
        };
        socket.current.onclose = () => {
            //console.log('WebSocket disconnected');
        };

        //Close Connection
        return () => {
            socket.current?.close();
        };

    }, [URL, onMessage]);

    
    // Function to ask question from LLM when a connected 
    const ask = useCallback(prompt => {
        if (socket.current?.readyState === WebSocket.OPEN) {
            socket.current.send(prompt);
        } 
        else {
            onMessage?.({"error":"Web Socket Not Ready"}); 
        }
    }, []);

    return { ask };
};
