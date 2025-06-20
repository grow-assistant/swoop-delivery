Skip to content
DoorDash


Mission & Values
Working at DoorDash
Belonging
Blogs
Career Areas
Engineering
University Careers
Search Jobs
Blog

Using ML and Optimization to Solve DoorDash’s Dispatch Problem
August 17, 2021

|
Alex Weinstein


DoorDash delivers millions of orders every day with the help of DeepRed, the system at the center of our last-mile logistics platform. But how does DeepRed really work and how do we use it to keep the marketplace running smoothly? To power our platform we needed to solve the “dispatch problem”: how to get each order from the store to the customer, via Dashers, as efficiently as possible. In this blog post, we will discuss the details of the dispatch problem, how we used ML and optimization to solve the problem, and how we continuously improve our solution with simulations and experimentation.

Understanding the dispatch problem
To better understand the dispatch problem we will take a look at the goals DeepRed tries to achieve for each part of our three sided market then we will examine the hurdles we face. 

The goals of dispatch
Let’s first define the goals we are trying to achieve when dispatching Dashers. Our goals are two-fold: 

Propose offers to Dashers as efficiently as possible so they can maximize their earning opportunities.
Deliver orders fast and on time so consumers and merchants are happy with their experience. 
Reaching these goals requires overcoming a number of challenges. We approach each challenge using machine learning and optimization solutions, and use simulation and experimentation methods to build on that performance.  

Finding the best Dasher 
To find the best Dasher to deliver an order, we need to consider a number of different factors. The most important factor is the geographical location of Dashers. We typically want to find a Dasher who is as close as possible to the store to minimize the total travel time. The second factor we look at is ensuring the Dasher will arrive at the right time. If we dispatch a Dasher too early, they will have to wait for the order to be ready. If we dispatch too late, the food will sit too long and could get cold, while the merchants and consumers become upset that the food wasn’t delivered as quickly as possible. Another factor is batching, utilizing Dashers as effectively as possible by looking for opportunities where a single Dasher can pick up multiple orders at the same store (or a set of nearby stores).


Figure 1 The goal of dispatch is to find the best Dasher to pick up each order once it’s ready at the merchant and deliver it to the customer. (This figure appeared in a previous blog post.)
Accounting for marketplace conditions
There are other marketplace conditions outside of our control that play into our decisions of which Dasher to choose. The most important one is the supply and demand balance in any given market. While we try to make sure there are enough Dashers available to fulfill orders, there may be times when we don’t have enough Dashers to pick up all the orders. In these undersupply scenarios, we have to make tradeoffs about which orders to pick up now versus later. These are also situations where it is beneficial to look for batching opportunities where a consumer can get their order faster if a single Dasher is able to pick up multiple orders at the same time. We also need to look at conditions like the weather and traffic that can impact delivery times or cause Dashers to refuse orders at higher rates than we would normally expect. For example, if it's raining and many Dashers use motorbikes we can expect fewer accepted deliveries, which can cause lateness and hurt our ability to complete our goals. 

Tackling the dispatch problem
Taking on such a complex problem was a two-stage process. First, we built a sophisticated dispatch service that utilizes a number of ML and optimization models to understand the state of the marketplace and make the best possible offers to Dashers to meet the needs of our marketplace. The second stage was to build simulation and experimentation platforms that would allow us to make continual improvements to our dispatch service. Both of these methods help us achieve our goals and continue to get 1% better every day. In the following sections, we will go through our dispatch system’s architecture and how it handles a sample delivery. Then we will describe how we leverage our simulation and experimentation platforms to improve our decisions. 

Building DeepRed: our dispatch service 
At a high level, the dispatch engine is built on two sets of mathematical models. The first set of models are ML models that are trained to estimate how an order will unfold if we offer it to a particular Dasher. These models are focused on making predictions about each individual order, store, and Dasher.

Stay Informed with Weekly Updates
Subscribe to our Engineering blog to get regular updates on all the coolest projects our team is working on

Email
 
Once the estimates are made they are fed into our second modeling layer, our mixed-integer optimization model. The optimization model makes the final recommendations about which orders to offer to which Dashers. Whereas the ML layers are focused on making individual estimates for each order, the optimization layer is focused on making system-wide decisions for the whole marketplace.

Taken together, the ML models and the optimization layer distill millions of data points from our marketplace into a set of dispatch decisions that ensure each order is offered to the Dasher who can deliver it from store to consumer as efficiently as possible.

An order’s journey through dispatch
The best way to understand how we solve the dispatch problem is to consider how an individual order works its way through DeepRed’s complex system. We’ll look at how an order passes through the multiple layers of DeepRed starting with our offer candidate generator, proceeding to our ML layer that estimates how those offers could play out in the real world, and then passing through our optimization layer that makes final recommendations.


Figure 2 Orders make their way through DeepRed’s three layers: offer generation, the ML layer, and our optimization model.
Constructing potential offers
When a new order arrives to our dispatch engine, we first update our understanding of the current state of the marketplace and how this order interacts with the Dashers and other orders. We are looking to find which Dashers are nearby and available to pick up the new order. These Dashers could be waiting for their next order, in which case we can offer them a new order right now, or they could be finishing up another order, in which case we can plan to offer them a new order as soon as they complete their current delivery.

Our focus at this stage is not limited to which Dashers are available: we also look at what other orders are waiting to be picked up. If there is another order being picked up at the same store or on the same block as our order, it may make sense to offer both orders to the same Dasher. The same can be true if there is another delivery that needs to be dropped off near where our order needs to be delivered.

By looking at the available Dashers and other orders, we are able to construct potential offers for our new order: a set of Dashers that this order could be offered to and possibly other orders that could be picked up by the same Dasher. These potential offers then get sent to the ML layer where we predict what might happen to these offers in the real world.

Predicting how an order will play out in the ML layer
With a set of potential offers in hand, we are ready to make some estimates using our ML models, including, but not limited to: order ready times, travel times, and offer acceptance likelihood.

The first question we want to answer using ML is when an order will be ready for pickup (order ready time). We estimate the order ready times based on a prep time model. A previous article, Solving for Unobserved Data in a Regression Model Using a Simple Data Adjustment, described how we estimate an order’s prep time and how we overcame the challenges of making a prediction with censored data.
The second set of questions our ML layer helps answer has to do with estimating travel times, the amount of time it will take a Dasher to travel to the store and then to deliver the order to the customer’s desired location. In addition to these travel times, there are multiple aspects of the Dasher journey that we model separately: how long it will take the Dasher to find parking at the merchant and consumer locations, how long it will take them to manage the logistics of picking up the order, and how long it will take them to return to their vehicle. Each of these steps of the order delivery journey requires a separate model. Some are based on tree models built on our Sibyl ML platform. Other estimates are based on simpler naive models. For example, we can estimate parking time at a particular store by using the average amount of time it took Dashers to find parking at that store over the past month.
A third and final question for our ML layer to answer is the likelihood each Dasher will accept the order if we offer it to them. Because Dashers have the freedom to accept or decline each offer, we work to anticipate the types of offers that are more likely to be accepted and present them to the most relevant Dasher. It is important to make sure every order is still delivered on time even if one or more Dashers turns down the offer before we find one who will accept it.
Once our new order passes through each of the three sets of models in our ML layer - order ready time, travel times, and acceptance rate - we now have a much better understanding of what we need to do to deliver the order as efficiently as possible. The rest of the work of making the final dispatch decision is up to our optimization layer.

Making final offers in the optimization layer
The optimization layer is our new order’s last stop in its journey before being dispatched to a Dasher. The optimization model does the work of scoring and ranking potential offers, making decisions about batching orders, and strategically delaying dispatches when necessary. 

Upon arriving in the optimization layer, our new order’s potential offers are scored and ranked to allow the mixed-integer program (MIP) to make its decisions, a process that we describe in a previous article, titled Next-Generation Optimization for Dasher Dispatch at DoorDash. Our scoring function is designed to recognize tradeoffs between efficiency (using Dasher time as efficiently as possible) and quality (getting deliveries to consumers as quickly as possible), while trying to account for explained and unexplained variance in our ML estimates of order ready times, travel times, and Dasher acceptance rate. Once every offer is scored, we solve the MIP using Gurobi, a software-based commercial MIP solver that is able to solve this type of problem at scale very efficiently.

In addition to scoring and ranking individual orders, the optimization model also considers which orders should be batched, i.e. served by the same single Dasher, to gain efficiency. Batching works particularly well when orders will be picked up from the same merchant, which reduces the number of pickup transactions, or multiple nearby merchants, which reduces the number of parking instances. The time it takes to prepare an order is actually helpful and can afford us extra time to pick up another order along the way, rather than simply delaying an offer to a Dasher. In some cases, batching leads to improvements in both efficient utilization of Dasher time, and faster order delivery -- especially when we don’t have a lot of Dashers available in that area. In other cases, we may be slightly delaying delivery time to help our Dashers get more earning opportunities from serving multiple simultaneous orders without violating our on-time promise to our customers. By making adjustments to the scoring function to accommodate batched orders and compare them to single orders, we allow the solver to make these tradeoffs efficiently for us.

An important final step before issuing final offer recommendations is to decide whether we choose the best available Dasher right now or delay the dispatch to choose a more optimal Dasher that might be available in the near future.. Another reason to delay dispatch is if we want to wait until closer to the order ready time so that the Dasher will not have to wait too long at the store. Using our dynamic dispatch engine, the optimization model is able to make the best tradeoff between dispatching right away or waiting.

After we score and rank offers, consider the best batches, and decide whether to delay dispatch, our order eventually completes its journey through dispatch. The order is offered to the Dasher we have chosen, and we wait to see if they will accept or decline the offer. If necessary, we will find another Dasher to offer the order to, until the order is picked up at the store and delivered to the happy customer. Our order has been dispatched!

Managing interactions between the ML and optimization layers
In our sample journey through dispatch, our new order passes through the ML layer and then the optimization layer in sequence before a Dasher is dispatched to pick up the order. But in reality there is a lot of complex interaction between our ML and optimization models. These interactions pose three important challenges that we addressed when building DeepRed.

Dealing with garbage in garbage out 
Avoiding overfitting 
Handling cascading variability 
Let’s go through these challenges one by one. 

The first problem could be termed garbage in, garbage out. In a previous article, Maintaining Machine Learning Model Accuracy Through Monitoring, we described how we monitor for model drift in our ML models. From DeepRed’s perspective, if our prep time or travel time predictions start to drift over time, the quality of our optimization will decline as well. For this reason, we continuously retrain our ML models and use rolling historical and real-time features that make sure the inputs to our models stay fresh.
The second challenge is the risk of overfitting parameters in our optimization model. Overfitting occurs when parameters are tuned precisely to conditions observed in the past, but result in suboptimal performance when given new inputs that may not match historic conditions. Even if our ML models are trained using regularization to avoid overfitting to the training data, we can still risk overfitting parameters in our optimization model if we tune our parameters naively based on empirical feedback to optimize short-term performance. We can fall into a local optimum trap where any improvements to the accuracy of our ML models fail to improve the global optimization output. To combat overfitting, we have implemented Bayesian optimization techniques to tune parameters in a robust, adaptive way.
The third challenge is cascading variability. Each of our ML models contributes variance to our model of what will happen upon offering a particular set of orders to a particular Dasher. This variability accumulates as a route becomes more complex or longer, for instance, via batching. We designed our scoring function to account for the added variance from more complex routes by adding a penalty term that scales with each of these forms of complexity and discourages DeepRed from making offers with high variability. 
By understanding and addressing the challenges posed by interactions between the ML and optimization layers, we designed DeepRed to be as robust as possible.

How we improve the dispatch service
Making improvements to the models that power dispatch is challenging both because our dispatch decisions are critical to DoorDash’s business and because any product changes can have complex interactions and downstream impacts throughout DeepRed. We employ two modeling approaches to mitigate this challenge: experimentation and simulation. Offline simulation helps us do early-stage exploration of product ideas to evaluate and anticipate their system-wide impacts before undertaking a large implementation effort. Rigorous experimentation helps us measure the holistic impact of all changes -- minor or substantial -- to the underlying ML or optimization models within dispatch. In this section, we’ll describe how we leverage our experimentation and simulation platforms to drive continuous improvements within DeepRed.


Figure 3 The lifecycle of a DeepRed product change to one of our ML or optimization models starts with simulation as a sandbox for ideas, and ends with experimentation in our marketplace.
Simulating real-world marketplace conditions
Simulation is a tool we can use to accelerate the pace and scale of innovation and understanding by prototyping new concepts and understanding potential impacts of product changes. There are some questions that are difficult to answer via experiment, such as the impact of product changes that require substantial engineering work across the platform, or how DeepRed will perform under different marketplace supply and demand conditions that we may not have observed historically in the real world.

Running simulations allows us to create counterfactual worlds where we can estimate how novel ideas or different environmental conditions would impact core performance metrics, without the downside risk of degrading customer experience or business metrics. The simulator we are building can imitate consumer, Dasher, and merchant behaviors interacting with the current or test dispatch system. Simulations give us insight about how the dispatch models perform in different operating conditions, including how efficiently we could handle high demand, low Dasher availability, and other likely future scenarios that we don’t observe today.

Testing product changes in production
Our experimentation platform helps us measure the actual performance of changes to our ML and optimization models based on key business metrics. We use experimentation methods to scientifically measure whether our improvements are actually moving the needle. With experimentation, there are two ways to ensure we get accurate measurements of the impact of product changes: thoughtful design and rigorous analysis.

The first approach is to be thoughtful about how we design our experiments. In a previous article, titled Switchback Tests and Randomized Experimentation Under Network Effects at DoorDash, we describe the challenge of experimentation in DoorDash’s marketplace setting and how we overcome network effects using switchback experimentation designs. In addition to network effects, we also have to worry about interaction effects between experiments. Because dispatch is so central to everything we do at DoorDash and the system is complex, we have a sizable team of data scientists and engineers running many experiments at the same time. With a weekly iteration cycle and lots of interacting experiments, we have sought ways to reduce the confidence intervals on our top-line metrics. One way we tackle this is by randomly splitting up our geographies and time periods each week into two separate groups. We use the first group to run a large number of exploratory experiments. In this group, we get a noisy initial measurement for these experiments. Experiments that show promising results from the first group can advance the following week to the second group where we run a select number of experiments (no more than three) to get a less noisy final measurement.
The second approach to accurate measurement is to be careful about how we analyze our experiments. Specifically, it is important to find ways to reduce variance in our estimators for efficiency and quality metrics. Some of our variance reduction methods, such as cluster robust standard error, have been discussed in a previous article. We also use post-hoc regression methods and analysis of interaction effects.
Building the right team
Building the right team is critical to tackle the complex set of challenges that the dispatch problem presents. To develop models in ML, optimization, experimentation, and simulation requires a diverse set of skills in data science. We have built and grown a dispatch data science team that is diversified across disciplines (OR, ML, causal inference, statistics) and industry experience (ridesharing, gig economy, Google).

Conclusion
The goal of dispatch at DoorDash is to find the right Dasher to deliver each order from  the merchant to the customer. The dispatch decisions we make define the experience our Dashers, customers, and merchants will have, and the efficiency with which our marketplace operates. To solve the dispatch problem, we used ML and optimization to build our dispatch engine DeepRed. We leaned on experimentation and simulation to make continuous improvements to DeepRed to keep things running as smoothly as possible. These efforts wouldn’t be possible without the diverse and talented Data Science team we’ve built to tackle this exciting set of problems.

About the Author
Alex Weinstein

Related Jobs
View All Jobs
Software Engineer, Frontend
Job ID: 3169453
Location
Pune, India
Department
Engineering
View Job
Senior Staff Software Engineer, Foundations Data
Job ID: 2815118
Location
San Francisco, CA; Sunnyvale, CA
Department
Engineering
View Job
Software Engineer - Developer Experience, Android
Job ID: 3167855
Location
San Francisco, CA; Sunnyvale, CA; Los Angeles, CA; Seattle, WA; New York, NY
Department
Engineering
View Job
Engineering Manager, DashPass Platform
Job ID: 2728459
Location
Seattle, WA
Department
Engineering
View Job
Principal Engineer, Product Security
Job ID: 3165012
Location
United States - Remote
Department
Engineering
View Job
Recent Blogs
View All Blogs
From Parenthood to Productivity: How DoorDash supported my maternity journey

culture
DoorDash
How we’re celebrating Indigenous Heritage Month at DoorDash

culture
DoorDash
How Strategy & Operations drives the DoorDash business forward

culture
strategy-operations
DoorDash
Careers Home
Mission & Values
Working at DoorDash
Belonging
Career Areas
University Careers
Career Blog
Talent Network
Search Jobs
Statement of Non-Discrimination: In keeping with our beliefs and goals, no employee or applicant will face discrimination or harassment based on: race, color, ancestry, national origin, religion, age, gender, marital/domestic partner status, sexual orientation, gender identity or expression, disability status, or veteran status. Above and beyond discrimination and harassment based on “protected categories,” we also strive to prevent other subtler forms of inappropriate behavior (i.e., stereotyping) from ever gaining a foothold in our office. Whether blatant or hidden, barriers to success have no place at DoorDash. We value a diverse workforce – people who identify as women, nonbinary or gender non-conforming, LGBTQIA+, American Indian or Native Alaskan, Black or African American, Hispanic or Latinx, Native Hawaiian or Other Pacific Islander, differently-abled, caretakers and parents, and veterans are strongly encouraged to apply. Thank you to the Level Playing Field Institute for this statement of non-discrimination.

Terms of Service
Consumer Privacy
Applicant Privacy Notice
© 2025 DoorDash