import * as BABYLON from 'babylonjs';

export class SceneManager {
  private readonly scene: BABYLON.Scene;

  constructor(scene: BABYLON.Scene) {
    this.scene = scene;
    this.configureScene();
  }

  private configureScene(): void {
    this.scene.clearColor = new BABYLON.Color4(0.06, 0.08, 0.12, 1);

    const light = new BABYLON.HemisphericLight('light', new BABYLON.Vector3(0, 1, 0), this.scene);
    light.intensity = 0.9;

    const ground = BABYLON.MeshBuilder.CreateGround('ground', { width: 20, height: 20 }, this.scene);
    ground.position.y = -1;

    const testSphere = BABYLON.MeshBuilder.CreateSphere('test-sphere', { diameter: 1.5 }, this.scene);
    testSphere.position.y = 1;
  }
}
