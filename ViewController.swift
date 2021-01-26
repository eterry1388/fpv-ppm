//
//  ViewController.swift
//  RadioController
//
//  Created by Eric Terry on 1/20/21.
//

import UIKit
import CoreMotion
import CoreLocation
import Starscream

class ViewController: UIViewController, WebSocketDelegate, CLLocationManagerDelegate {
    var socket: WebSocket!
    var isConnected = false
    let server = WebSocketServer()

    override func viewDidLoad() {
        super.viewDidLoad()

        var request = URLRequest(url: URL(string: "http://192.168.1.3:8080")!)
        request.timeoutInterval = 5
        socket = WebSocket(request: request)
        socket.delegate = self
        socket.connect()

        startAccelerometers()
    }

    var touchX = CGFloat()
    var touchY = CGFloat()

    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {
        let touch = touches.first!
        let location = touch.location(in: self.view)
        self.touchX = location.x
        self.touchY = location.y
    }

    func didReceive(event: WebSocketEvent, client: WebSocket) {
        switch event {
        case .connected(let headers):
            isConnected = true
            print("websocket is connected: \(headers)")
        case .disconnected(let reason, let code):
            isConnected = false
            print("websocket is disconnected: \(reason) with code: \(code)")
        case .text(let string):
            print("Received text: \(string)")
        case .binary(let data):
            print("Received data: \(data.count)")
        case .ping(_):
            break
        case .pong(_):
            break
        case .viabilityChanged(_):
            break
        case .reconnectSuggested(_):
            break
        case .cancelled:
            isConnected = false
        case .error(let error):
            isConnected = false
            handleError(error)
        }
    }

    func handleError(_ error: Error?) {
        if let e = error as? WSError {
            print("websocket encountered an error: \(e.message)")
        } else if let e = error {
            print("websocket encountered an error: \(e.localizedDescription)")
        } else {
            print("websocket encountered an error")
        }
    }

    let motion = CMMotionManager()
    let location = CLLocationManager()
    var timer = Timer()

    func startAccelerometers() {
       // Make sure the accelerometer hardware is available.
        if self.motion.isAccelerometerAvailable && self.motion.isMagnetometerAvailable && self.motion.isDeviceMotionAvailable {
            self.motion.accelerometerUpdateInterval = 1.0 / 60.0  // 60 Hz
            self.motion.magnetometerUpdateInterval = 1.0 / 60.0  // 60 Hz
            self.motion.deviceMotionUpdateInterval = 1.0 / 60.0  // 60 Hz
            self.motion.startAccelerometerUpdates()
            self.motion.startMagnetometerUpdates()
            self.motion.startDeviceMotionUpdates()

            self.location.requestAlwaysAuthorization()
            self.location.startUpdatingHeading()

          // Configure a timer to fetch the data.
          self.timer = Timer(fire: Date(), interval: (1.0/60.0), repeats: true, block: { (timer) in
            // Get the accelerometer data.
            let accData = self.motion.accelerometerData
            let magData = self.motion.magnetometerData
            let motData = self.motion.deviceMotion
            let heading = self.location.heading!.trueHeading

            if accData != nil && magData != nil && motData != nil {
                let accX = accData!.acceleration.x
                let accY = accData!.acceleration.y

                let magX = magData!.magneticField.x
                let magY = magData!.magneticField.y
                let magZ = magData!.magneticField.z

                let graX = motData!.gravity.x
                let graY = motData!.gravity.y
                let graZ = motData!.gravity.z

                let uaccX = motData!.userAcceleration.x
                let uaccY = motData!.userAcceleration.y
                let uaccZ = motData!.userAcceleration.z

                self.socket.write(string: "{ \"accX\": \"\(accX)\", \"accY\": \"\(accY)\", \"magX\": \"\(magX)\", \"magY\": \"\(magY)\", \"magZ\": \"\(magZ)\", \"graX\": \"\(graX)\", \"graY\": \"\(graY)\", \"graZ\": \"\(graZ)\", \"uaccX\": \"\(uaccX)\", \"uaccY\": \"\(uaccY)\", \"uaccZ\": \"\(uaccZ)\", \"heading\": \"\(heading)\", \"touchX\": \"\(self.touchX)\", \"touchY\": \"\(self.touchY)\" }")
             }
          })

          // Add the timer to the current run loop.
          RunLoop.current.add(self.timer, forMode: RunLoop.Mode.default)
       }
    }
}
