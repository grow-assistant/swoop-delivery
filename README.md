# Optimized On-Course Delivery Assignment System

## Overview

This document outlines a rule-based logic system for optimizing on-course food and beverage deliveries at a golf course. The system is designed to ensure golfer satisfaction by providing fast and efficient service.

The scenario involves an 18-hole golf course with the following assets:
*   **2 Beverage Carts:** Each cart services a specific 9-hole loop (Front 9 and Back 9).
*   **3 Mobile Delivery Staff:** These staff members can move freely across the entire course.

All personnel are equipped with GPS trackers, and the course is mapped with dynamic geofences for each hole to pinpoint order and staff locations accurately. When a golfer places an order, a smart dispatch algorithm assigns the delivery to the most suitable candidate based on their location, availability, and the defined operational rules.

## Key Components & Constraints

*   **GPS Tracking:** All beverage carts and delivery staff have real-time GPS tracking, providing full visibility of their locations on the course.
*   **Dynamic Geofencing:** The course is divided into 18 zones, one for each hole. This allows the system to instantly map an order's origin and identify nearby staff.
*   **Beverage Cart Zone Restrictions:** Each beverage cart is restricted to its designated 9-hole loop (Holes 1-9 or 10-18) to maintain operational efficiency.
*   **Mobile Delivery Staff:** The three delivery staff members are not restricted by zones and can handle multiple orders simultaneously.
*   **Request/Accept/Decline Mechanism:** The system offers deliveries to candidates via a notification. The candidate must accept the offer to be assigned the delivery.
*   **No Penalties for Declines:** Staff are not penalized for declining a delivery offer. The system simply moves to the next best candidate.
*   **Priorities:** The primary goals of the dispatch logic are **speed** (minimizing delivery time) and **efficiency** (reducing travel distance and balancing workload).
*   **Rule-Based Engine:** The initial implementation uses a deterministic, rule-based engine for decision-making.

## Assignment Algorithm Flow (Rule-Based)

The assignment process follows a logical sequence from order placement to completion.

### 1. Order Received & Zone Identification
When a golfer places an order, the system captures their GPS location and maps it to a specific geofenced zone (e.g., "Hole 4"). This automatically identifies the relevant course segment (e.g., "Front 9") and the corresponding beverage cart.

### 2. Select Eligible Delivery Candidates
The system compiles a list of all potential candidates who can take the delivery. This is done by applying the following filters:
*   **Zone Restriction:** Only the beverage cart assigned to the order's half of the course is considered.
*   **Proximity Check:** Delivery staff within a reasonable distance of the order location are included.
*   **Availability & Capacity:** The system checks the current status of each candidate. Staff who are free or have the capacity to take on another order are considered eligible. The system can also consider staff who are about to complete a delivery as "soon-to-be-available."

### 3. Rank Candidates
Eligible candidates are ranked using a scoring system to determine who gets the first offer. The ranking is based on:
*   **Proximity & ETA:** The estimated time for the candidate to complete the delivery. Closer and faster candidates receive a higher score.
*   **Current Workload:** Candidates who are completely free are generally ranked higher than those already handling other orders.

### 4. Offer Dispatch & Acceptance Loop
The system initiates a request-and-accept loop:
1.  The top-ranked candidate receives a notification with the order details and options to **Accept** or **Decline**.
2.  The candidate has a short time window (e.g., 15 seconds) to respond.
3.  If they **accept**, the order is assigned, and the loop ends.
4.  If they **decline** or do not respond, the system immediately offers the order to the next candidate in the ranked list.
5.  This process repeats until a candidate accepts the assignment.

### 5. Assignment Confirmation & Routing
Once a candidate accepts:
*   The assignment is finalized.
*   The delivery person receives the optimal route to the pickup location (if any) and then to the golfer.
*   The golfer can be notified that their order is on its way with an estimated ETA.
*   If a staff member is assigned multiple orders, the system provides an intelligently sequenced route to ensure all deliveries are made efficiently.

### 6. Live Tracking & Status Updates
The system monitors the delivery in real-time:
*   The dispatcher can view the live GPS location of the assigned staff.
*   The golfer's app can display an updated ETA.
*   The system can detect potential delays and trigger alerts for manual intervention if needed (e.g., reassigning the order).

### 7. Delivery Completion & Logging
Upon completion of the delivery:
1.  The staff member marks the order as "Delivered" in their app.
2.  The system logs the completion time and other relevant data (e.g., total delivery time).
3.  The staff member's status is updated to "Available" for new assignments.

## Calculating Beverage Cart ETA

To accurately estimate the arrival time for a beverage cart on its fixed loop, the following model is used.

### 1. Pre-Mapped Loop Segments
*   **Digitize the Loop Path:** The cart's route for each 9-hole loop is divided into directional segments connecting each hole (e.g., Segment 1: Hole 1 → Hole 2, Segment 2: Hole 2 → Hole 3, etc.).
*   **Store Travel Times per Segment:** An average travel time is measured and stored for each segment under normal conditions. This creates a time-weighted, directed loop.

**Example Data Table:**
| Segment     | From Hole | To Hole | Avg. Time (min) |
|-------------|-----------|---------|-----------------|
| Segment 1   | 1         | 2       | 2.0             |
| Segment 2   | 2         | 3       | 3.0             |
| ...         | ...       | ...     | ...             |
| Segment 9   | 9         | 1       | 2.5             |

### 2. ETA Calculation Logic
1.  **Determine Current Location:** The system uses GPS to find the cart's current segment (e.g., "between Hole 4 and 5").
2.  **Determine Request Location:** The target hole for the delivery is identified (e.g., "Hole 2").
3.  **Calculate ETA:** The system traces the path forward along the pre-defined loop from the cart's current position to the target hole, summing the average travel times of all segments in between. Carts do not reverse direction.

**Example Calculation:**
*   **Cart Location:** Between Hole 4 and 5.
*   **Target:** Hole 2.
*   **Path:** 5→6→7→8→9→1→2
*   **ETA:** Sum of travel times for segments (5→6), (6→7), (7→8), (8→9), (9→1), and (1→2). 