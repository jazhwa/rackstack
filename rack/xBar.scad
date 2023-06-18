include <../helper/cylindricalFilet.scad>
include <../helper/filet.scad>
include <../helper/screws.scad>
include <../helper/matrix.scad>

include <./config.scad>
include <./sharedVariables.scad>
include <./connector/connectors.scad>

*xBar();

module xBar() {

  applyConnector(on="xBar", to="yBar", trans=xBarMirrorOtherCornerTrans * xBarYBarConnectorTrans)
  applyConnector(on="xBar", to="yBar", trans=xBarYBarConnectorTrans)
  xBarBase();

  module xBarBase() {
    intersection() {

      difference() {
        cylindricalFiletEdge(xBarY, xBarX, xBarHeight, xBarRoundness);

        union() {
          translate(v = [xBarWallThickness, xBarSideThickness, xBarWallThickness])
          cylindricalFiletEdge(xBarY, xBarX-2*xBarSideThickness, xBarHeight, xBarRoundness-xBarWallThickness);

          connectorWallFiletNegative();

          multmatrix(xBarMirrorOtherCornerTrans)
          connectorWallFiletNegative();
        }
      }

      // Shave off bottom corners to reduce elephant's foot at where xBar and YBar join
      halfspace(vpos = [0, 1, 1], p = [0, 0.75, 0]);
      halfspace(vpos = [0, -1, 1], p = [0, xBarX-0.75, 0]);
    }


    module connectorWallFiletNegative() {
      cylindricalFiletNegative(
        p0=[xBarWallThickness, xBarSideThickness, xBarHeight],
        p1=[xBarY, xBarSideThickness, xBarHeight],
        n=[0, 1, 1], r=2
      );
    }

  }

}

xBarYBarConnectorTrans = rotate(a=[0,0,-90]);

xBarMirrorOtherCornerTrans = translate(v = [0, xBarX, 0]) * mirror(v = [0, 1, 0]);