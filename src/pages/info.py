import streamlit as st


def show_page():
    st.title("📖 Info Page")
    st.header("Welcome to the Great Fantasy Bake Off League!")
    st.markdown(
        """
    On your marks, get set, predict! This season, we’re adding a new layer of fun to our weekly viewing with a fantasy league. 
    The goal is simple: prove you have the best eye for baking talent by accurately predicting both the weekly events and the season's ultimate champions.
    """
    )
    st.markdown("---")

    st.subheader("How to Play: Your Weekly Signature Bake")
    st.markdown(
        """
    Each week of the competition (starting with Episode 2), you will submit a fresh set of predictions before the episode airs.
    Your weekly submission must now include **six** predictions:
    - **Star Baker**: Who will be the week's top baker?
    - **Technical Challenge Winner**: Who will come in first in the technical?
    - **Baker Sent Home**: Who will be eliminated from the competition?
    - **Hollywood Handshake**: Will anyone get a handshake? (Optional, high-reward pick).
    - **Predicted Season Winner**: Who do you think will win the entire competition?
    - **Predicted Finalists (x2)**: Who will the other two finalists be?

    Your predictions for the season winner and finalists can change week to week as you see how the bakers perform.
    """
    )
    st.markdown("---")

    st.subheader("Scoring: The Recipe for Victory")
    st.markdown(
        "Your grand total will be a combination of two types of points: **Weekly Points** and **Foresight Points**."
    )

    st.write("#### 1. Weekly Points")
    st.markdown(
        """These are straightforward points for correctly predicting the episode's key events.
    __Note: Points are may be awarded or penalized, as shown below.__
    __There is no penalty for saying there will be no handshake and one is given.__
    """
    )
    st.markdown(
        """
    | Correct Prediction                 | Points Awarded |
    |------------------------------------|----------------|
    | Handshake Predicted and Given      | 10 points      |
    | Star Baker                         | 5 points       |
    | Baker Sent Home                    | 5 points       |
    | Technical Challenge Winner         | 3 points       |

    | Penalties                          | Points Removed |
    |------------------------------------|----------------|
    | Handshake Predicted, None Given    | 10 points      |
    | Predicted Star Baker is sent home  | 5 points       |
    | Predicted Baker Sent Home is Star  | 5 points       |
    """
    )

    st.write("#### 2. Foresight Points: The Weighted Bonus")
    st.markdown(
        """
    This is where strategy comes in. You get points for correctly predicting the season's winner and finalists, 
    but correct predictions made **earlier in the season are worth exponentially more**.

    Your season outcome predictions are logged each week but scores will only be known when the winner is crowned. 
    At the end of the season, we'll go back and award points for every single time you correctly predicted the outcome.
    - **The Formula**: A correct pick is multiplied by a factor that decreases each week. A correct **winner** prediction is worth **10 base points**, and a correct **finalist** is worth **5**.
    - **Example**: Correctly predicting the season winner in Week 2 is worth **90 points** `((11-2) x 10)`. Waiting until the semi-final in Week 9 to make that same correct prediction is only worth **20 points** `((11-9) x 10)`.
    This is cumulative, so correct predictions in, for example, Weeks 3, 6, 8, and 10 would all be included in your total.
    """
    )
