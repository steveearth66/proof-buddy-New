To get started with Lab 9 on Proof Buddy, follow the steps outlined below: 

1. Go to https://proofbuddy.net/ and click “Sign Up”. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-28 at 18.55.08.png)


2. Choose “student” (you won’t have access to the lab if you sign up as an “instructor”!) 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-28 at 18.57.36.png)


3. For the username, enter your abc123 Drexel ID (without the “@drexel.edu”) but then do include it underneath your email. Do NOT forget your password since it takes 24+ hours for the reset password feature to update. (If you do forget, you can create a second account with the same email but different username) 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-28 at 19.00.39.png)

4. It may take a second or two when it first creates your account, but once it does, it should automatically take you back to the first screen where you can click the “log in” to take you to the usual (non-account creation) login page. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-28 at 19.07.18.png)


5. This is the usual login page. Enter your username and password and click the LOGIN button (avoid using “forget password” since you won’t get it in time to do the lab in class). It’s recommended to save your login credentials in your browser or password manager. 


![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-28 at 19.08.02.png)
 

6. Make sure “Type of Proof” is set to Equational Reasoning (that’s the default) and click “Let's Begin”. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-28 at 19.10.49.png) 

7. In the top left, enter the name of the proof as “Q1” (or “Q2” if you’re on the second question of the lab etc). For the tag, enter “Lab09” (or whatever lab you are doing.) Now, click Definitions from the Proof Utilities menu. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-28 at 21.24.39.png) 

8. When doing Question 1, enable the function F (for Q2 you would disable F and enable H etc.). You might have to use the scroll bar to see the function you want. Twist the wedge on the right to expand the details, so you can click the Enable/Disable button. (Note: in the future, you can go here to create your own functions if desired). Now hit the red button on the bottom left to close the Definitions window. You can return to this at any time to review definitions. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-29 at 20.37.11.png)  

9. For the “LHS Goal” field, enter whatever the question is asking you to evaluate. For Q1, you would put (F 5 1) observe that the parentheses get surrounded by small red boundaries to indicate they are matched (useful for longer expressions). In the RHS goal, you should enter the number that you think the answer will be -- you should think about this first! It’s okay if you just take a guess and get it wrong, but you won’t get the cool “Proof Complete” confetti at the end unless you get it right. You should leave the Current LHS/RHS fields blank (the program automatically fills those in as you make the proof). The blue highlight around the “Current LHS” is to indicate that we will be operating on the lefthand side of the equation (i.e. the racket function, not the integer on the righthand side). For this lab, you will never have to go to the right-hand side, so there is never a need to switch sides! (if you do switch accidentally, you can simply toggle back) 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-29 at 20.39.11.png)  
 

10. After clicking “Start Equational Reasoning Proof” the top parameter frame with the goals becomes uneditable. The middle frame displays your proof. All your inputs will happen in the bottom frame. The start of the proof (line000, the premise) is given to you already. To create the next line of the proof, click the 001 box in the proof display, or instead you can enter 001 in the number field in the input pane. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-29 at 20.47.34.png)   

 
11. Notice that as soon as you select a line for binding, a targeting yellow highlight appears on the line above (just leave it alone for now since its default position is actually where we want it). In the editing frame (the bottom third panel), say (without the quote marks) “apply F with a↦5, b↦1” You can get the mapping symbol ↦ simply by pressing the = key. For this lab, the only rules you need to use are “apply” for a function definition, and “eval” for a built-in racket function on given integers. But if you want to see others, you can click the “view rule set” option under proof utilities. When you’re ready to check that your proposed rule is applicable and to automatically generate the Racket expression, click the “Generate and Check” button. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-29 at 20.50.34.png)
 

12. The racket for line001 has been generated. You should double check that it matches what you manually predicted it would be when you wrote it down in your lab. The new yellow highlight is the Result highlight; i.e. the new part of the expression that came from applying the rule (in this case, everything is new so the entire line is highlighted!) The color of the Result highlight will always pair with the color of the prior Target Highlight.  

Note: if you get a “could not find rule associated with F” error msg, it is possible you typed a lower case f rather than upper case F. Another possibility is that you forgot to enable the F definition. Since the allowable functions become locked in once you start the proof, you will have to clear the proof (via Proof Utilities) to enable it. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-29 at 20.54.33.png)


13. Throughout this lab, you’ll be repeating these same four steps: [1] click a line num to bind for editing (in this case 002) [2] click in the PREVIOUS expression above it to highlight the new target (blue) that you want to change. Everything outside the blue will stay the same. Use the arrow keys to move around the expression. In this case, since it started with the entire thing highlighted, you first hit DOWN to enter into the parentheses. Right/Left moves within parentheses. UP moves you outside of the current parentheses you’re in. In this case, after hitting Down, we’d hit Right once to select the entire subexpression (zero? 1) [3] enter the rule to use on the blue target highlight (in this case, eval zero?, and don’t forget the ? as that is part of the function name) [4] click Generate and Check. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-30 at 21.07.21.png) 
 

14. You should see something like this. Observe that in the newly generated line002, it is exactly the same as the previous line EXCEPT that the (zero? 1) has been replaced with #f (the result of evaluating the zero? Function on 1), which has the blue Result-highlight (matching the blue of the target-highlight). 

Note: the yellow highlight in line001 was the result-highlight from the previous line. The vertical line left border colors are another indicator of their meaning. (the split color of Blue/Red on the line002 rule tells you that the rule “eval zero?” is how we transformed from line001 (blue) to line002 (red), and that the new targeting highlight color for line002 will be red. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-30 at 21.10.59.png) 

 

15. For the next proof step, we wish to evaluate the if function. A common mistake when doing an “eval if” is to try to do so before knowing whether then first argument is #t or #f. Another common mistake is to target-highlight just the #f or just the if. The correct thing to do is target the entire if expression in red as shown in the picture (this includes the if function as well as all three of its inputs). To do so, since the red-default highlight is initially just on the #f, we need to use the UP arrow key. (if pushing the arrow keys doesn’t move the red target highlight, make sure the focus is in the line002 expression by clicking somewhere in it first) 

Alert: #f is the boolean for false, which is totally different from the function F defined in Q1. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-30 at 21.18.23.png)
 

 

16. You have successfully completed the proof when you have transformed the premise on the LHS into the goal you entered for the RHS. Doing so will trigger a confetti animation which can be dismissed by clicking anywhere. 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-30 at 21.24.52.png) 
 

17. Harder proofs that you will learn later in the course won’t trigger automatically, and you will have to push the “Check Proof” button under Proof Utilities to determine completion. When you’re ready to go to the next problem, click Clear Proof. Don’t forget to put “Q2” as the new name, and “Lab09” as the tag. As before, go to Definition and be sure to Enable the function H (and disable the F since you won’t need it anymore). 

![alt text](/Users/ahsannadeem/Desktop/Proof Buddy Images/Screenshot 2026-01-30 at 21.26.09.png) 


Note: your professor might require a screenshot of your proof (or “proof complete” statement) on your lab/homework, so be sure to do that before clearing!